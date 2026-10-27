import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import AppError, error_body
from app.core.logging import request_id_var, setup_logging

log = logging.getLogger("suvnazorat")


@asynccontextmanager
async def lifespan(_: FastAPI):  # type: ignore[no-untyped-def]
    settings = get_settings()
    settings.validate_for_production()
    setup_logging(settings.log_level)
    log.info("SuvNazorat backend ishga tushdi (env=%s)", settings.app_env)

    if settings.app_env == "test":
        yield
        return

    # Ochiq Telegram kanallarini avtomatik monitoring qilish (bot admin bo'lmasa ham)
    async def channel_polling_loop() -> None:
        from app.db.session import session_scope
        from app.services.channel_scraper import sync_all_active_channels

        def _sync_worker() -> None:
            with session_scope() as db:
                sync_all_active_channels(db, days_back=1)

        while True:
            try:
                await asyncio.sleep(45)
                await asyncio.to_thread(_sync_worker)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.debug("Kanal polling xatoligi: %s", e)

    poll_task = asyncio.create_task(channel_polling_loop())
    yield
    poll_task.cancel()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="SuvNazorat API", version="0.1.0", lifespan=lifespan)

    origins = list(
        set(
            [
                settings.frontend_url,
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:8000",
                "http://127.0.0.1:8000",
            ]
        )
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        rid = uuid.uuid4().hex[:12]
        request_id_var.set(rid)
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        headers = {}
        if exc.status_code == 429 and isinstance(exc.details, dict):
            headers["Retry-After"] = str(exc.details.get("retry_after_seconds", 60))
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message, exc.details),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=error_body("validation_error", "Yuborilgan ma'lumotlar noto'g'ri.", details),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
        # Ichki xatolik tafsilotlari mijozga qaytarilmaydi; faqat logga yoziladi.
        log.error("Kutilmagan xatolik: %s", type(exc).__name__, exc_info=exc)
        return JSONResponse(
            status_code=500, content=error_body("internal_error", "Ichki xatolik yuz berdi.")
        )

    app.include_router(api_router)
    return app


app = create_app()
