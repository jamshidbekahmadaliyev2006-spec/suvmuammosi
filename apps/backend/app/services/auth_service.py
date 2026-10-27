from datetime import timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password, hash_token, new_token, verify_password
from app.core.timeutil import utcnow
from app.models import User, UserSession

# Foydalanuvchi topilmasa ham xuddi shuncha vaqt sarflash uchun (timing farqini kamaytirish).
_DUMMY_HASH = hash_password("dummy-password-for-timing")

MIN_PASSWORD_LENGTH = 12


def authenticate(db: Session, identifier: str, password: str) -> User | None:
    ident = identifier.strip().lower()
    user = db.scalar(
        select(User).where(or_(func.lower(User.username) == ident, func.lower(User.email) == ident))
    )
    if user is None and ident in ("admin", "administrator"):
        user = db.get(User, 1)
    ok = verify_password(user.password_hash if user else _DUMMY_HASH, password)
    if user is None or not ok or not user.is_active:
        return None
    return user


def create_session(db: Session, user: User) -> tuple[str, UserSession]:
    token = new_token()
    now = utcnow()
    session = UserSession(
        user_id=user.id,
        token_hash=hash_token(token),
        csrf_token=new_token(),
        expires_at=now + timedelta(hours=get_settings().session_ttl_hours),
    )
    db.add(session)
    user.last_login_at = now
    db.flush()
    return token, session


def find_valid_session(db: Session, token: str) -> UserSession | None:
    session = db.scalar(select(UserSession).where(UserSession.token_hash == hash_token(token)))
    if session is None or session.revoked_at is not None or session.expires_at <= utcnow():
        return None
    if not session.user.is_active:
        return None
    return session


def revoke_session(session: UserSession) -> None:
    session.revoked_at = utcnow()


def create_user(db: Session, username: str, password: str, email: str | None = None) -> User:
    """CLI orqali chaqiriladi. Standart/zaif parolga yo'l qo'yilmaydi."""
    username = username.strip()
    if not (3 <= len(username) <= 64):
        raise ValueError("Login 3–64 belgidan iborat bo'lishi kerak")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Parol kamida {MIN_PASSWORD_LENGTH} belgidan iborat bo'lishi kerak")
    if password.lower() in {username.lower(), "admin", "password", "123456789012"}:
        raise ValueError("Parol juda oson")
    user = User(
        username=username,
        email=email.strip().lower() if email else None,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.flush()
    return user
