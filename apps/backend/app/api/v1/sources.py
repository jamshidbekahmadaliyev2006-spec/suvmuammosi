from typing import Annotated, Any

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbDep
from app.schemas.common import Page
from app.schemas.source import (
    SourceCreate,
    SourceOut,
    SourcePatch,
    SourceResolveIn,
    SourceResolveOut,
    SyncHistoryIn,
    SyncHistoryOut,
)
from app.services import source_service as svc

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=Page[SourceOut])
def list_sources(
    db: DbDep,
    _: CurrentUser,
    q: str | None = None,
    is_active: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 20,
) -> Page[SourceOut]:
    items, total = svc.list_sources(db, q=q, is_active=is_active, page=page, page_size=page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.post("/resolve", response_model=SourceResolveOut)
def resolve_source(data: SourceResolveIn, _: CurrentUser) -> SourceResolveOut:
    """Telegram havola yoki username orqali kanal/guruh parametrlarini avtomatik aniqlash."""
    res = svc.resolve_telegram_source(data.identifier)
    return SourceResolveOut(**res)


@router.post("/sync-history", response_model=SyncHistoryOut)
def sync_history(
    db: DbDep,
    _: CurrentUser,
    data: SyncHistoryIn | None = None,
) -> SyncHistoryOut:
    """Barcha faol Telegram kanallarining so'nggi 10 kunlik (yoki ko'rsatilgan) postlarini olib keladi va kalit so'zlar bo'yicha hodisalarni aniqlaydi."""
    from app.services.channel_scraper import rescan_messages_with_rules, sync_all_active_channels
    days = data.days_back if data else 10
    results = sync_all_active_channels(db, days_back=days)
    rescanned = rescan_messages_with_rules(db)
    return SyncHistoryOut(
        status="ok",
        synced_sources=len(results),
        total_messages_synced=sum(results.values()),
        rescanned_incidents=rescanned,
    )


@router.post("/{source_id}/sync")
def sync_single_source(
    source_id: int,
    db: DbDep,
    _: CurrentUser,
    days_back: Annotated[int, Query(ge=1, le=30)] = 10,
) -> dict[str, Any]:
    """Aynan bitta manbani so'nggi N kunlik postlarini sinxronlash."""
    from app.services.channel_scraper import rescan_messages_with_rules, sync_source_channel_posts
    source = svc.get_source(db, source_id)
    cnt = sync_source_channel_posts(db, source, days_back=days_back)
    rescanned = rescan_messages_with_rules(db)
    return {
        "status": "ok",
        "source_id": source_id,
        "messages_synced": cnt,
        "rescanned_incidents": rescanned,
    }


@router.post("", response_model=SourceOut, status_code=201)
def create(data: SourceCreate, db: DbDep, user: CurrentUser) -> SourceOut:
    return svc.create_source(db, data, user.id)  # type: ignore[return-value]


@router.get("/{source_id}", response_model=SourceOut)
def get(source_id: int, db: DbDep, _: CurrentUser) -> SourceOut:
    return svc.get_source(db, source_id)  # type: ignore[return-value]


@router.patch("/{source_id}", response_model=SourceOut)
def patch(source_id: int, data: SourcePatch, db: DbDep, user: CurrentUser) -> SourceOut:
    return svc.update_source(db, source_id, data, user.id)  # type: ignore[return-value]


@router.delete("/{source_id}", status_code=204)
def delete(source_id: int, db: DbDep, user: CurrentUser) -> None:
    svc.delete_source(db, source_id, user.id)

