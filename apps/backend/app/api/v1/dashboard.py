from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbDep
from app.schemas.dashboard import BotStatusOut, DashboardStats
from app.schemas.incident import IncidentListItem, MessageOut
from app.services import dashboard_service as svc

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/stats", response_model=DashboardStats)
def stats(db: DbDep, _: CurrentUser) -> DashboardStats:
    return svc.get_stats(db)


@router.get("/dashboard/recent-incidents", response_model=list[IncidentListItem])
def recent_incidents(
    db: DbDep,
    _: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    report_type: str | None = None,
) -> list[IncidentListItem]:
    return svc.recent_incidents(db, limit, report_type)  # type: ignore[return-value]


@router.get("/dashboard/recent-messages", response_model=list[MessageOut])
def recent_messages(
    db: DbDep, _: CurrentUser, limit: Annotated[int, Query(ge=1, le=50)] = 10
) -> list[MessageOut]:
    return svc.recent_messages(db, limit)  # type: ignore[return-value]


@router.get("/system/bot-status", response_model=BotStatusOut)
def bot_status(db: DbDep, _: CurrentUser) -> BotStatusOut:
    return svc.bot_status(db)
