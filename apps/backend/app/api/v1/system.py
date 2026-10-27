from typing import Any

import httpx
from fastapi import APIRouter, Response
from pydantic import BaseModel
from sqlalchemy import text

from app.api.deps import CurrentUser, DbDep
from app.core.config import get_settings
from app.core.errors import AppError
from app.services import settings_service

router = APIRouter(prefix="/system", tags=["system"])


class AdminPhonesIn(BaseModel):
    phones: list[str]


@router.get("/health")
def health(db: DbDep, response: Response) -> dict[str, str]:
    """Ochiq health-check: hech qanday konfiguratsiya yoki maxfiy qiymat qaytarmaydi."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        response.status_code = 503
        return {"status": "degraded", "database": "down"}
    return {"status": "ok", "database": "up"}


@router.get("/admin-phones")
def get_admin_phones(db: DbDep, _: CurrentUser) -> dict[str, list[str]]:
    return {"phones": settings_service.get_admin_phones(db)}


@router.post("/admin-phones")
def set_admin_phones(data: AdminPhonesIn, db: DbDep, _: CurrentUser) -> dict[str, Any]:
    saved = settings_service.set_admin_phones(db, data.phones)
    db.commit()
    return {"ok": True, "phones": saved}


@router.get("/media/{file_id}")
async def get_media(file_id: str, response: Response):
    token = get_settings().telegram_bot_token
    if not token:
        raise AppError(404, "bot_not_configured", "Telegram bot token mavjud emas.")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            info_res = await client.get(f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}")
            if info_res.status_code != 200:
                raise AppError(404, "media_not_found", "Telegram media fayli topilmadi.")
            file_path = info_res.json().get("result", {}).get("file_path")
            if not file_path:
                raise AppError(404, "media_path_not_found", "Fayl yo'li topilmadi.")
            file_res = await client.get(f"https://api.telegram.org/file/bot{token}/{file_path}")
            if file_res.status_code != 200:
                raise AppError(404, "download_failed", "Faylni yuklab olish imkoni bo'lmadi.")

            content_type = file_res.headers.get("content-type", "image/jpeg")
            return Response(content=file_res.content, media_type=content_type)
    except AppError:
        raise
    except Exception as exc:
        raise AppError(500, "media_error", f"Media yuklashda xatolik: {exc}")
