from datetime import timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.timeutil import today_bounds_utc, utcnow
from app.models import (
    Incident,
    IncidentComment,
    IncidentStatusHistory,
    MonitoringSource,
    SourceMessage,
)
from app.models.enums import IncidentCategory, IncidentStatus, ProcessingStatus, SourceType
from app.schemas.dashboard import BotStatusOut, DashboardStats, SourceActivity, StatsCards
from app.services import settings_service


def bot_status(db: Session) -> BotStatusOut:
    """Faqat haqiqiy heartbeat bo'lsa ONLINE; hech qachon kelmagan bo'lsa UNKNOWN."""
    hb = settings_service.get_setting(db, settings_service.BOT_HEARTBEAT)
    if not hb:
        return BotStatusOut(
            status="UNKNOWN", last_heartbeat_at=None, rules_version=None, rules_loaded=None,
            detail="Bot hali heartbeat yubormagan.",
        )
    from datetime import datetime

    at = datetime.fromisoformat(hb["at"])
    fresh = utcnow() - at <= timedelta(seconds=get_settings().bot_heartbeat_ttl_seconds)
    loaded = bool(hb.get("rules_loaded"))
    if not fresh:
        status, detail = "OFFLINE", "Oxirgi heartbeat eskirgan."
    elif not loaded:
        status, detail = "DEGRADED", "Bot ishlayapti, lekin qoidalar hali yuklanmagan."
    else:
        status, detail = "ONLINE", "Bot ishlayapti."
    return BotStatusOut(
        status=status, last_heartbeat_at=at, rules_version=hb.get("rules_version"),
        rules_loaded=loaded, detail=detail,
    )


def _count(db: Session, stmt) -> int:  # type: ignore[no-untyped-def]
    return db.scalar(stmt) or 0


def get_stats(db: Session) -> DashboardStats:
    day_start, day_end = today_bounds_utc()

    by_status = {s: 0 for s in IncidentStatus}
    for status, n in db.execute(select(Incident.status, func.count()).group_by(Incident.status)):
        by_status[status] = n
    by_category = {c: 0 for c in IncidentCategory}
    for cat, n in db.execute(select(Incident.category, func.count()).group_by(Incident.category)):
        by_category[cat] = n

    has_history = select(IncidentStatusHistory.incident_id).where(
        IncidentStatusHistory.incident_id == Incident.id
    ).exists()
    has_comment = select(IncidentComment.incident_id).where(
        IncidentComment.incident_id == Incident.id
    ).exists()
    unreviewed = _count(
        db,
        select(func.count()).select_from(Incident).where(
            Incident.status == IncidentStatus.OPEN, ~has_history, ~has_comment
        ),
    )
    # Faqat real fuqarolar murojaati va arizalari (Zayavkalar) bo'yicha chora ko'rish ko'rsatkichlari:
    # OAV va yangiliklar (NEWS) hech qachon hal qilinmagan qizil avariya hisoblanmaydi!
    zayavka_open = _count(
        db,
        select(func.count()).select_from(Incident).where(
            Incident.report_type.in_(["ZAYAVKA", "MUROJAAT"]),
            Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.IN_PROGRESS]),
        ),
    )
    zayavka_resolved = _count(
        db,
        select(func.count()).select_from(Incident).where(
            Incident.report_type.in_(["ZAYAVKA", "MUROJAAT", "GRATITUDE"]),
            Incident.status == IncidentStatus.RESOLVED,
        ),
    )
    news_count = _count(
        db,
        select(func.count()).select_from(Incident).where(
            Incident.report_type.in_(["NEWS", "ANNOUNCEMENT"]),
            Incident.status != IncidentStatus.INVALID,
        ),
    )
    total_zayavkas = zayavka_open + zayavka_resolved

    cards = StatsCards(
        total_incidents=total_zayavkas,
        open_incidents=zayavka_open,
        in_progress_incidents=0,
        resolved_incidents=zayavka_resolved,
        news_count=news_count,
        total_zayavkas=total_zayavkas,
        messages_today=_count(
            db,
            select(func.count()).select_from(SourceMessage).where(
                SourceMessage.received_at >= day_start, SourceMessage.received_at < day_end
            ),
        ),
        unreviewed_incidents=zayavka_open,
        review_required_messages=_count(
            db,
            select(func.count()).select_from(SourceMessage).where(
                SourceMessage.processing_status == ProcessingStatus.REVIEW_REQUIRED
            ),
        ),
        channels_and_groups_count=_count(
            db,
            select(func.count()).select_from(MonitoringSource).where(
                MonitoringSource.source_type.in_([SourceType.CHANNEL, SourceType.GROUP])
            ),
        ),
    )

    since = utcnow() - timedelta(hours=24)
    counts = dict(
        db.execute(
            select(SourceMessage.source_id, func.count())
            .where(SourceMessage.received_at >= since)
            .group_by(SourceMessage.source_id)
        ).all()
    )
    sources = [
        SourceActivity(
            source_id=s.id, name=s.name, is_active=s.is_active,
            messages_24h=counts.get(s.id, 0), last_message_at=s.last_message_at,
        )
        for s in db.scalars(
            select(MonitoringSource)
            .where(MonitoringSource.source_type.in_([SourceType.CHANNEL, SourceType.GROUP]))
            .order_by(MonitoringSource.name)
        )
    ]
    return DashboardStats(
        cards=cards, by_status=by_status, by_category=by_category, sources=sources,
        bot=bot_status(db),
        last_sync_at=db.scalar(select(func.max(SourceMessage.received_at))),
        day_start_utc=day_start, day_end_utc=day_end,
    )


def recent_incidents(db: Session, limit: int, report_type: str | None = None) -> list[Incident]:
    stmt = select(Incident)
    if report_type:
        rt = report_type.upper()
        if rt in ("ZAYAVKA", "MUROJAAT"):
            stmt = stmt.where(Incident.report_type.in_(["ZAYAVKA", "MUROJAAT"]))
        elif rt in ("NEWS", "YANGILIK"):
            stmt = stmt.where(Incident.report_type.in_(["NEWS", "YANGILIK"]))
        elif rt in ("ANNOUNCEMENT", "GRATITUDE", "ELON"):
            stmt = stmt.where(Incident.report_type.in_(["ANNOUNCEMENT", "GRATITUDE", "RASMIY_ELON", "TASHAKKUR"]))
        else:
            stmt = stmt.where(Incident.report_type == rt)
    else:
        # Standart holatda zayavkalar (murojaatlar) doimo birinchi o'rinda ko'rinadi
        is_zayavka = case({True: 1}, value=Incident.report_type.in_(["ZAYAVKA", "MUROJAAT"]), else_=0)
        is_open = case({True: 1}, value=Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.IN_PROGRESS]), else_=0)
        stmt = stmt.order_by(
            is_zayavka.desc(),
            is_open.desc(),
            func.coalesce(Incident.last_seen_at, Incident.first_seen_at).desc(),
            Incident.id.desc(),
        )
        return list(db.scalars(stmt.limit(limit)).unique().all())

    stmt = stmt.order_by(
        func.coalesce(Incident.last_seen_at, Incident.first_seen_at).desc(),
        Incident.id.desc(),
    ).limit(limit)
    return list(db.scalars(stmt).unique().all())


def recent_messages(db: Session, limit: int) -> list[SourceMessage]:
    stmt = (
        select(SourceMessage)
        .where(SourceMessage.processing_status != ProcessingStatus.NO_MATCH)
        .order_by(SourceMessage.received_at.desc(), SourceMessage.id.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).unique().all())
