from datetime import date

from sqlalchemy import case, exists, func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.timeutil import local_day_bounds_utc, utcnow
from app.models import (
    Incident,
    IncidentComment,
    IncidentMessage,
    IncidentStatusHistory,
    SourceMessage,
)
from app.models.enums import IncidentCategory, IncidentStatus, Priority
from app.schemas.incident import IncidentPatch
from app.services import audit
from app.services.text import like_pattern

_PRIORITY_RANK = case(
    {Priority.HIGH: 3, Priority.MEDIUM: 2, Priority.LOW: 1}, value=Incident.priority
)
SORT_FIELDS = {
    "first_seen_at": Incident.first_seen_at,
    "last_seen_at": Incident.last_seen_at,
    "created_at": Incident.created_at,
    "status": Incident.status,
    "priority": _PRIORITY_RANK,
}


def get_incident(db: Session, incident_id: int) -> Incident:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise AppError(404, "incident_not_found", "Hodisa topilmadi.")
    return incident


def list_incidents(
    db: Session,
    *,
    q: str | None = None,
    status: IncidentStatus | None = None,
    category: IncidentCategory | None = None,
    report_type: str | None = None,
    source_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort_by: str = "first_seen_at",
    order: str = "desc",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Incident], int]:
    stmt = select(Incident)
    if q and q.strip():
        like = like_pattern(q)
        stmt = stmt.where(
            or_(Incident.title.ilike(like, escape="\\"), Incident.description.ilike(like, escape="\\"))
        )
    if report_type:
        rt = report_type.upper()
        if rt in ("ZAYAVKA", "MUROJAAT", "ARIZA"):
            stmt = stmt.where(Incident.report_type.in_(["ZAYAVKA", "MUROJAAT", "ARIZA"]))
        elif rt in ("NEWS", "YANGILIK"):
            stmt = stmt.where(Incident.report_type.in_(["NEWS", "YANGILIK"]))
        elif rt in ("ANNOUNCEMENT", "RASMIY_ELON", "ELON"):
            stmt = stmt.where(Incident.report_type.in_(["ANNOUNCEMENT", "RASMIY_ELON", "ELON"]))
        elif rt in ("GRATITUDE", "MINNATDORCHILIK", "TASHAKKUR"):
            stmt = stmt.where(Incident.report_type.in_(["GRATITUDE", "MINNATDORCHILIK", "TASHAKKUR"]))
        elif rt in ("IRRELEVANT", "NOTOGRI", "REKLAMA"):
            stmt = stmt.where(Incident.report_type.in_(["IRRELEVANT", "NOTOGRI", "REKLAMA"]))
        else:
            stmt = stmt.where(Incident.report_type == rt)
    if status:
        stat_upper = str(status).upper()
        if stat_upper in ("OPEN", "UNRESOLVED"):
            stmt = stmt.where(Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.IN_PROGRESS]))
        elif stat_upper == "RESOLVED":
            stmt = stmt.where(Incident.status == IncidentStatus.RESOLVED)
        else:
            stmt = stmt.where(Incident.status == status)
    if category:
        stmt = stmt.where(Incident.category == category)
    if source_id:
        # Asosiy manba yoki bog'langan xabarlardan birining manbasi.
        linked = exists().where(
            IncidentMessage.incident_id == Incident.id,
            IncidentMessage.source_message_id == SourceMessage.id,
            SourceMessage.source_id == source_id,
        )
        stmt = stmt.where(or_(Incident.source_id == source_id, linked))
    if date_from:
        stmt = stmt.where(Incident.first_seen_at >= local_day_bounds_utc(date_from)[0])
    if date_to:
        stmt = stmt.where(Incident.first_seen_at < local_day_bounds_utc(date_to)[1])

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    column = SORT_FIELDS[sort_by]
    tie_breaker = Incident.id.asc() if order == "asc" else Incident.id.desc()
    stmt = stmt.order_by(column.asc() if order == "asc" else column.desc(), tie_breaker)
    items = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).unique().all()
    return list(items), total


def first_message(db: Session, incident_id: int) -> SourceMessage | None:
    return db.scalar(
        select(SourceMessage)
        .join(IncidentMessage, IncidentMessage.source_message_id == SourceMessage.id)
        .where(IncidentMessage.incident_id == incident_id)
        .order_by(SourceMessage.telegram_timestamp, SourceMessage.id)
        .limit(1)
    )


def list_messages(db: Session, incident_id: int) -> list[SourceMessage]:
    return list(
        db.scalars(
            select(SourceMessage)
            .join(IncidentMessage, IncidentMessage.source_message_id == SourceMessage.id)
            .where(IncidentMessage.incident_id == incident_id)
            .order_by(SourceMessage.telegram_timestamp, SourceMessage.id)
        )
        .unique()
        .all()
    )


def list_history(db: Session, incident_id: int) -> list[IncidentStatusHistory]:
    return list(
        db.scalars(
            select(IncidentStatusHistory)
            .where(IncidentStatusHistory.incident_id == incident_id)
            .order_by(IncidentStatusHistory.created_at.desc(), IncidentStatusHistory.id.desc())
        )
        .unique()
        .all()
    )


def list_comments(db: Session, incident_id: int) -> list[IncidentComment]:
    return list(
        db.scalars(
            select(IncidentComment)
            .where(IncidentComment.incident_id == incident_id)
            .order_by(IncidentComment.created_at, IncidentComment.id)
        )
        .unique()
        .all()
    )


def update_incident(db: Session, incident_id: int, data: IncidentPatch, user_id: int) -> Incident:
    """Holatni faqat tizim foydalanuvchisi o'zgartiradi (bot RESOLVED qila olmaydi)."""
    incident = get_incident(db, incident_id)
    changes = data.model_dump(exclude_unset=True, exclude={"comment", "status"})
    for key, value in changes.items():
        if value is None and key in {"priority", "category"}:
            continue
        setattr(incident, key, value)

    new_status = data.status
    if new_status is not None and new_status != incident.status:
        db.add(
            IncidentStatusHistory(
                incident_id=incident.id,
                old_status=incident.status,
                new_status=new_status,
                changed_by_user_id=user_id,
                comment=data.comment,
            )
        )
        audit.log_action(
            db, user_id=user_id, action="incident.status_change", entity_type="incident",
            entity_id=incident.id,
            details={"old": incident.status.value, "new": new_status.value},
        )
        incident.resolved_at = utcnow() if new_status == IncidentStatus.RESOLVED else None
        incident.status = new_status
    elif changes:
        audit.log_action(
            db, user_id=user_id, action="incident.update", entity_type="incident",
            entity_id=incident.id, details={"fields": sorted(changes)},
        )
    db.commit()
    db.refresh(incident)
    return incident


def add_comment(db: Session, incident_id: int, text: str, user_id: int) -> IncidentComment:
    incident = get_incident(db, incident_id)
    comment = IncidentComment(incident_id=incident.id, user_id=user_id, comment=text)
    db.add(comment)
    db.flush()
    audit.log_action(
        db, user_id=user_id, action="incident.comment", entity_type="incident",
        entity_id=incident.id, details={"comment_id": comment.id},
    )
    db.commit()
    db.refresh(comment)
    return comment
