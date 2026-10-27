"""Autentifikatsiya bog'liqliklari: cookie-sessiya + CSRF, va bot API kaliti."""
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import safe_equals
from app.db.session import get_db
from app.models import User
from app.services import auth_service

SESSION_COOKIE = "sn_session"
CSRF_HEADER = "x-csrf-token"
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

DbDep = Annotated[Session, Depends(get_db)]


def require_user(request: Request, db: DbDep) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    session = auth_service.find_valid_session(db, token) if token else None
    if session is None:
        raise AppError(401, "not_authenticated", "Tizimga kirish talab qilinadi.")
    if request.method in UNSAFE_METHODS:
        sent = request.headers.get(CSRF_HEADER, "")
        if not safe_equals(sent, session.csrf_token):
            raise AppError(403, "csrf_failed", "Xavfsizlik tekshiruvi muvaffaqiyatsiz.")
    request.state.session = session
    return session.user


def require_bot(x_bot_api_key: Annotated[str | None, Header()] = None) -> None:
    expected = get_settings().telegram_bot_api_key
    if not expected or not x_bot_api_key or not safe_equals(x_bot_api_key, expected):
        raise AppError(401, "invalid_bot_key", "Bot kaliti noto'g'ri yoki yuborilmagan.")


def require_user_or_bot(
    request: Request, db: DbDep, x_bot_api_key: Annotated[str | None, Header()] = None
) -> None:
    if x_bot_api_key is not None:
        require_bot(x_bot_api_key)
    else:
        require_user(request, db)


CurrentUser = Annotated[User, Depends(require_user)]
BotAuth = Depends(require_bot)
UserOrBotAuth = Depends(require_user_or_bot)
