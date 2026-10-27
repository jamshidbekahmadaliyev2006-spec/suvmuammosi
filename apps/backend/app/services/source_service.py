import hashlib
import logging
from typing import Any

import httpx
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models import Incident, IncidentMessage, MonitoringSource, SourceMessage
from app.models.enums import SourceType

from app.schemas.source import SourceCreate, SourcePatch
from app.services import audit
from app.services.text import like_pattern

log = logging.getLogger("suvnazorat.sources")


import re

def clean_username(value: str | None) -> str | None:
    """Telegram havola yoki foydalanuvchi nomidan toza usernameni ajratadi."""
    if not value:
        return None
    val = value.strip()
    for prefix in [
        "https://t.me/",
        "http://t.me/",
        "t.me/",
        "https://telegram.me/",
        "http://telegram.me/",
        "telegram.me/",
    ]:
        if val.lower().startswith(prefix):
            val = val[len(prefix):]
            break
    val = val.lstrip("@").strip()
    val = val.split("?")[0].split("/")[0].strip()
    if not val:
        return None
    if not re.match(r"^[A-Za-z0-9_]{3,64}$", val):
        raise AppError(422, "invalid_username", "Telegram username faqat harflar, raqamlar va pastki chiziqdan iborat bo'lishi kerak.")
    return val


def resolve_telegram_source(identifier: str) -> dict[str, Any]:
    """Kanal/guruh havolasi yoki usernamesi bo'yicha Telegramdan haqiqiy Chat ID, nom va turni topadi."""
    username = clean_username(identifier)
    if not username:
        raise AppError(422, "invalid_identifier", "Telegram username yoki havolasi kiritilmadi.")

    settings = get_settings()
    token = settings.telegram_bot_token or settings.telegram_bot_api_key

    resolved_info: dict[str, Any] | None = None

    if token:
        try:
            with httpx.Client(timeout=4.0) as client:
                res = client.get(
                    f"https://api.telegram.org/bot{token}/getChat",
                    params={"chat_id": f"@{username}"},
                )
                if res.status_code == 200:
                    data = res.json().get("result", {})
                    chat_id = data.get("id")
                    title = data.get("title") or username
                    chat_type = data.get("type")
                    src_type = (
                        SourceType.CHANNEL
                        if chat_type == "channel"
                        else SourceType.GROUP
                    )
                    resolved_info = {
                        "telegram_chat_id": chat_id,
                        "name": title,
                        "telegram_username": data.get("username") or username,
                        "source_type": src_type,
                        "resolved": True,
                    }
        except Exception as e:
            log.warning("Telegram getChat xatoligi (@%s): %s", username, e)

    if not resolved_info:
        # Fallback: Agar Telegram API ga ulanib bo'lmasa, deterministik chat_id generatsiya qilinadi
        h = int(hashlib.sha256(username.lower().encode()).hexdigest()[:12], 16)
        synthetic_id = -1000000000000 - (h % 900000000000)
        resolved_info = {
            "telegram_chat_id": synthetic_id,
            "name": username,
            "telegram_username": username,
            "source_type": SourceType.CHANNEL,
            "resolved": False,
        }

    return resolved_info


def get_source(db: Session, source_id: int) -> MonitoringSource:
    source = db.get(MonitoringSource, source_id)
    if source is None:
        raise AppError(404, "source_not_found", "Manba topilmadi.")
    return source


def create_source(db: Session, data: SourceCreate, user_id: int) -> MonitoringSource:
    raw_user = clean_username(data.telegram_username) or clean_username(data.name)
    chat_id = data.telegram_chat_id
    name = data.name.strip() if data.name else None
    src_type = data.source_type or SourceType.CHANNEL

    # Agar chat_id berilmagan bo'lsa, avtomatik resolve qilamiz
    if chat_id is None:
        if not raw_user:
            raise AppError(422, "missing_identifier", "Telegram kanal yoki guruh username/havolasini kiriting.")
        resolved = resolve_telegram_source(raw_user)
        chat_id = resolved["telegram_chat_id"]
        if not name or name == raw_user:
            name = resolved["name"]
        raw_user = resolved["telegram_username"]
        src_type = resolved["source_type"]

    if not name:
        name = raw_user or f"Telegram Chat {chat_id}"

    existing = db.scalar(
        select(MonitoringSource.id).where(MonitoringSource.telegram_chat_id == chat_id)
    )
    if existing is not None:
        raise AppError(409, "source_exists", "Bu Telegram chat ID allaqachon qo'shilgan.")

    source = MonitoringSource(
        name=name,
        telegram_chat_id=chat_id,
        telegram_username=raw_user,
        source_type=src_type,
        is_active=data.is_active,
    )
    db.add(source)
    db.flush()
    audit.log_action(
        db,
        user_id=user_id,
        action="source.create",
        entity_type="monitoring_source",
        entity_id=source.id,
        details={"chat_id": source.telegram_chat_id, "name": source.name},
    )
    db.commit()
    db.refresh(source)

    # Kanal postlarini darhol sinxronlash (agar bot admin bo'lmasa ham)
    try:
        from app.services.channel_scraper import sync_source_channel_posts
        sync_source_channel_posts(db, source)
    except Exception as e:
        log.debug("Kanal postlarini darhol sinxronlashda xatolik: %s", e)

    return source


def get_or_create_bot_source(db: Session) -> MonitoringSource:
    """Fuqarolar murojaatlari uchun markaziy tizim bot manbasini qaytaradi yoki yaratadi."""
    bot_source = db.scalar(
        select(MonitoringSource).where(MonitoringSource.source_type == SourceType.BOT)
    )
    if bot_source is None:
        bot_source = MonitoringSource(
            name="Telegram Bot (Murojaatlar)",
            telegram_chat_id=0,
            source_type=SourceType.BOT,
            telegram_username="hokimyatsuvnazorati_bot",
            is_active=True,
        )
        db.add(bot_source)
        db.flush()
    return bot_source


def delete_source(db: Session, source_id: int, user_id: int) -> bool:
    """Manbani va unga tegishli xabarlarni xavfsiz o'chiradi."""
    source = get_source(db, source_id)
    bot_source = get_or_create_bot_source(db)

    # 1. Bog'langan xabarlar ID larini aniqlash
    msg_ids = list(
        db.scalars(select(SourceMessage.id).where(SourceMessage.source_id == source.id)).all()
    )
    if msg_ids:
        # Bog'langan hodisa xabarlarini o'chirish
        db.execute(delete(IncidentMessage).where(IncidentMessage.source_message_id.in_(msg_ids)))
        # Xabarlarni o'chirish
        db.execute(delete(SourceMessage).where(SourceMessage.id.in_(msg_ids)))

    # 2. Ushbu manbaga biriktirilgan hodisalarni bot manbasiga ko'chirish
    if source.id != bot_source.id:
        db.execute(
            update(Incident)
            .where(Incident.source_id == source.id)
            .values(source_id=bot_source.id)
        )

    # 3. Manbani o'chirish
    db.delete(source)
    audit.log_action(
        db,
        user_id=user_id,
        action="source.delete",
        entity_type="monitoring_source",
        entity_id=source.id,
        details={"name": source.name, "chat_id": source.telegram_chat_id},
    )
    db.commit()
    return True


def update_source(db: Session, source_id: int, data: SourcePatch, user_id: int) -> MonitoringSource:
    source = get_source(db, source_id)
    changes = data.model_dump(exclude_unset=True)

    if "telegram_username" in changes and changes["telegram_username"]:
        changes["telegram_username"] = clean_username(changes["telegram_username"])

    if "telegram_chat_id" in changes and changes["telegram_chat_id"] is not None:
        cid = changes["telegram_chat_id"]
        existing = db.scalar(
            select(MonitoringSource.id).where(
                MonitoringSource.telegram_chat_id == cid,
                MonitoringSource.id != source.id,
            )
        )
        if existing is not None:
            raise AppError(409, "source_exists", "Bu Telegram chat ID allaqachon qo'shilgan.")

    for key, value in changes.items():
        if value is None and key != "telegram_username":
            continue
        setattr(source, key, value)

    audit.log_action(
        db,
        user_id=user_id,
        action="source.update",
        entity_type="monitoring_source",
        entity_id=source.id,
        details={"fields": sorted(changes)},
    )
    db.commit()
    db.refresh(source)
    return source


def list_sources(
    db: Session, *, q: str | None, is_active: bool | None, page: int, page_size: int
) -> tuple[list[MonitoringSource], int]:
    # Faqat Kanal va Guruhlar ko'rsatiladi (Bot tizim manbasi alohida ajratilgan)
    stmt = select(MonitoringSource).where(
        MonitoringSource.source_type.in_([SourceType.CHANNEL, SourceType.GROUP])
    )
    if q and q.strip():
        like = like_pattern(q)
        stmt = stmt.where(
            or_(
                MonitoringSource.name.ilike(like, escape="\\"),
                MonitoringSource.telegram_username.ilike(like, escape="\\"),
            )
        )
    if is_active is not None:
        stmt = stmt.where(MonitoringSource.is_active == is_active)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.order_by(MonitoringSource.id.desc()).offset((page - 1) * page_size).limit(page_size)
    return list(db.scalars(stmt).all()), total

