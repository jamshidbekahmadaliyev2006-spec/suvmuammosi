from fastapi import APIRouter, Request, Response

from app.api.deps import SESSION_COOKIE, CurrentUser, DbDep
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import hash_password, verify_password
from app.schemas.auth import LoginIn, ProfileUpdateIn, SessionOut, UserOut
from app.services import audit, auth_service
from app.services.rate_limit import login_limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=SessionOut)
def login(data: LoginIn, request: Request, response: Response, db: DbDep) -> SessionOut:
    settings = get_settings()
    ip = request.client.host if request.client else "unknown"
    key = f"{ip}|{data.identifier.strip().lower()}"
    wait = login_limiter.retry_after(key, settings.login_max_attempts, settings.login_window_seconds)
    if wait:
        raise AppError(
            429, "too_many_attempts", "Urinishlar ko'p. Keyinroq qayta urinib ko'ring.",
            {"retry_after_seconds": wait},
        )
    user = auth_service.authenticate(db, data.identifier, data.password)
    if user is None:
        login_limiter.record_failure(key)
        audit.log_action(db, user_id=None, action="auth.login_failed", entity_type="user")
        db.commit()
        # Hisob mavjudligi haqida ma'lumot bermaydigan umumiy xabar.
        raise AppError(401, "invalid_credentials", "Login yoki parol noto'g'ri.")
    login_limiter.reset(key)
    token, session = auth_service.create_session(db, user)
    audit.log_action(db, user_id=user.id, action="auth.login", entity_type="user", entity_id=user.id)
    db.commit()
    response.set_cookie(
        SESSION_COOKIE, token, httponly=True, secure=settings.cookie_secure, samesite="lax",
        max_age=settings.session_ttl_hours * 3600, path="/",
    )
    return SessionOut(user=UserOut.model_validate(user), csrf_token=session.csrf_token)


@router.post("/logout")
def logout(request: Request, response: Response, user: CurrentUser, db: DbDep) -> dict[str, bool]:
    auth_service.revoke_session(request.state.session)
    audit.log_action(db, user_id=user.id, action="auth.logout", entity_type="user", entity_id=user.id)
    db.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@router.get("/me", response_model=SessionOut)
def me(request: Request, user: CurrentUser) -> SessionOut:
    return SessionOut(
        user=UserOut.model_validate(user), csrf_token=request.state.session.csrf_token
    )


@router.patch("/profile", response_model=UserOut)
def update_profile(data: ProfileUpdateIn, user: CurrentUser, db: DbDep) -> UserOut:
    if data.username is not None:
        new_username = data.username.strip()
        if len(new_username) < 3:
            raise AppError(400, "invalid_username", "Login kamida 3 belgidan iborat bo'lishi kerak.")
        if new_username != user.username:
            from sqlalchemy import func
            existing = (
                db.query(user.__class__)
                .filter(
                    func.lower(user.__class__.username) == new_username.lower(),
                    user.__class__.id != user.id,
                )
                .first()
            )
            if existing:
                raise AppError(400, "username_taken", "Ushbu login band, boshqa login tanlang.")
            user.username = new_username

    if data.email is not None:
        user.email = data.email.strip().lower() or None

    if data.new_password:
        if not data.current_password:
            raise AppError(400, "password_required", "Parolni o'zgartirish uchun joriy parolni kiriting.")
        if not verify_password(user.password_hash, data.current_password):
            raise AppError(400, "wrong_password", "Joriy parol noto'g'ri kiritildi.")
        if len(data.new_password) < 8:
            raise AppError(400, "short_password", "Yangi parol kamida 8 ta belgidan iborat bo'lishi kerak.")
        user.password_hash = hash_password(data.new_password)

    audit.log_action(db, user_id=user.id, action="user.profile_update", entity_type="user", entity_id=user.id)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)

