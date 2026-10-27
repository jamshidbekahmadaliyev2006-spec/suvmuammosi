from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbDep
from app.models.enums import IncidentCategory, IncidentStatus
from app.schemas.common import Page
from app.schemas.incident import (
    CommentIn,
    CommentOut,
    HistoryOut,
    IncidentDetail,
    IncidentListItem,
    IncidentPatch,
    MessageOut,
)
from app.services import incident_service as svc

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _detail(db: DbDep, incident_id: int) -> IncidentDetail:
    incident = svc.get_incident(db, incident_id)
    base = IncidentListItem.model_validate(incident).model_dump()
    base.pop("description", None)
    base.pop("resolution_notes", None)
    base.pop("resolved_at", None)
    first = svc.first_message(db, incident.id)
    return IncidentDetail(
        **base,
        description=incident.description,
        resolution_notes=incident.resolution_notes,
        resolved_at=incident.resolved_at,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        first_message=MessageOut.model_validate(first) if first else None,
        comments=[CommentOut.model_validate(c) for c in svc.list_comments(db, incident.id)],
    )


@router.get("", response_model=Page[IncidentListItem])
def list_incidents(
    db: DbDep,
    _: CurrentUser,
    q: str | None = None,
    status: str | None = None,
    category: IncidentCategory | None = None,
    report_type: str | None = None,
    source_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort_by: Literal["first_seen_at", "last_seen_at", "created_at", "status", "priority"] = (
        "first_seen_at"
    ),
    order: Literal["asc", "desc"] = "desc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Page[IncidentListItem]:
    items, total = svc.list_incidents(
        db, q=q, status=status, category=category, report_type=report_type, source_id=source_id,
        date_from=date_from, date_to=date_to, sort_by=sort_by, order=order,
        page=page, page_size=page_size,
    )
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{incident_id}", response_model=IncidentDetail)
def get_incident(incident_id: int, db: DbDep, _: CurrentUser) -> IncidentDetail:
    return _detail(db, incident_id)


@router.patch("/{incident_id}", response_model=IncidentDetail)
def patch_incident(
    incident_id: int, data: IncidentPatch, db: DbDep, user: CurrentUser
) -> IncidentDetail:
    svc.update_incident(db, incident_id, data, user.id)
    return _detail(db, incident_id)


@router.get("/{incident_id}/history", response_model=list[HistoryOut])
def history(incident_id: int, db: DbDep, _: CurrentUser) -> list[HistoryOut]:
    svc.get_incident(db, incident_id)
    return svc.list_history(db, incident_id)  # type: ignore[return-value]


@router.get("/{incident_id}/messages", response_model=list[MessageOut])
def messages(incident_id: int, db: DbDep, _: CurrentUser) -> list[MessageOut]:
    svc.get_incident(db, incident_id)
    return svc.list_messages(db, incident_id)  # type: ignore[return-value]


@router.post("/{incident_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(incident_id: int, data: CommentIn, db: DbDep, user: CurrentUser) -> CommentOut:
    return svc.add_comment(db, incident_id, data.comment, user.id)  # type: ignore[return-value]
