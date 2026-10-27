from typing import Any

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import BotAuth, DbDep
from app.core.timeutil import utcnow
from app.models import Incident, MonitoringSource
from app.models.enums import IncidentStatus
from app.schemas.bot import (
    BotCancelIncidentIn,
    BotMessageIn,
    BotMessageOut,
    BotSourceRegisterIn,
    HeartbeatIn,
)
from app.services import ingest_service, settings_service

router = APIRouter(prefix="/bot", tags=["bot"], dependencies=[BotAuth])


@router.post("/messages", response_model=BotMessageOut)
def receive_message(data: BotMessageIn, db: DbDep) -> BotMessageOut:
    return ingest_service.ingest_message(db, data)


@router.get("/summary")
def get_bot_summary(db: DbDep) -> dict[str, Any]:
    """Admin yoki mas'ul xodim uchun bot orqali tezkor monitoring ma'lumotlari."""
    total = db.scalar(select(func.count(Incident.id))) or 0
    open_cnt = db.scalar(select(func.count(Incident.id)).where(Incident.status == IncidentStatus.OPEN)) or 0
    in_prog = db.scalar(select(func.count(Incident.id)).where(Incident.status == IncidentStatus.IN_PROGRESS)) or 0
    resolved = db.scalar(select(func.count(Incident.id)).where(Incident.status == IncidentStatus.RESOLVED)) or 0
    sources_cnt = db.scalar(select(func.count(MonitoringSource.id)).where(MonitoringSource.is_active == True)) or 0

    recent = db.scalars(
        select(Incident).order_by(Incident.created_at.desc()).limit(5)
    ).all()

    return {
        "total": total,
        "open": open_cnt,
        "in_progress": in_prog,
        "resolved": resolved,
        "sources_count": sources_cnt,
        "recent": [
            {
                "id": inc.id,
                "title": inc.title,
                "district": inc.district or "Toshkent sh.",
                "category": inc.category.value if inc.category else "OTHER",
                "priority": inc.priority.value if inc.priority else "MEDIUM",
                "status": inc.status.value,
                "created_at": inc.created_at.strftime("%H:%M, %d.%m.%Y") if inc.created_at else None,
            }
            for inc in recent
        ],
    }


@router.post("/heartbeat")
def heartbeat(data: HeartbeatIn, db: DbDep) -> dict[str, bool]:
    settings_service.set_setting(
        db,
        settings_service.BOT_HEARTBEAT,
        {
            "at": utcnow().isoformat(),
            "bot_version": data.bot_version,
            "rules_version": data.rules_version,
            "rules_loaded": data.rules_loaded,
            "rules_fetched_at": data.rules_fetched_at.isoformat() if data.rules_fetched_at else None,
            "watched_sources": data.watched_sources,
        },
    )
    db.commit()
    return {"ok": True}


@router.post("/register-source")
def register_source(data: BotSourceRegisterIn, db: DbDep) -> dict[str, Any]:
    source = db.scalar(
        select(MonitoringSource).where(MonitoringSource.telegram_chat_id == data.chat_id)
    )
    if source is not None:
        source.is_active = True
        if data.chat_title:
            source.name = data.chat_title
        if data.chat_username:
            source.telegram_username = data.chat_username
        db.commit()
        return {"ok": True, "created": False, "source_id": source.id, "name": source.name}

    new_source = MonitoringSource(
        name=data.chat_title or f"Telegram Chat {data.chat_id}",
        telegram_chat_id=data.chat_id,
        source_type=data.source_type,
        telegram_username=data.chat_username,
        is_active=True,
    )
    db.add(new_source)
    db.commit()
    db.refresh(new_source)
    return {"ok": True, "created": True, "source_id": new_source.id, "name": new_source.name}


@router.get("/check-admin")
def check_admin(phone: str, db: DbDep) -> dict[str, Any]:
    return {"is_admin": settings_service.is_admin_phone(db, phone), "phone": phone}


@router.post("/cancel-incident")
def cancel_incident(data: BotCancelIncidentIn, db: DbDep) -> dict[str, Any]:
    """Fuqaro Telegram bot orqali o'z murojaatini bekor qilganda."""
    incident = db.get(Incident, data.incident_id)
    if incident is not None:
        incident.status = IncidentStatus.INVALID
        incident.resolution_notes = "Foydalanuvchi tomonidan Telegram bot orqali bekor qilindi."
        db.commit()
        return {"ok": True, "cancelled": True, "incident_id": incident.id}
    return {"ok": False, "error": "incident_not_found"}


