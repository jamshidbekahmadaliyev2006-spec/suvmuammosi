from datetime import datetime

from pydantic import BaseModel

from app.models.enums import IncidentCategory, IncidentStatus


class StatsCards(BaseModel):
    total_incidents: int
    open_incidents: int
    in_progress_incidents: int
    resolved_incidents: int
    messages_today: int
    unreviewed_incidents: int  # OPEN, hali tarix yoki izohi yo'q
    review_required_messages: int
    channels_and_groups_count: int = 53
    news_count: int = 0
    total_zayavkas: int = 0


class SourceActivity(BaseModel):
    source_id: int
    name: str
    is_active: bool
    messages_24h: int
    last_message_at: datetime | None


class BotStatusOut(BaseModel):
    status: str  # ONLINE | DEGRADED | OFFLINE | UNKNOWN
    last_heartbeat_at: datetime | None
    rules_version: int | None
    rules_loaded: bool | None
    detail: str


class DashboardStats(BaseModel):
    cards: StatsCards
    by_status: dict[IncidentStatus, int]
    by_category: dict[IncidentCategory, int]
    sources: list[SourceActivity]
    bot: BotStatusOut
    last_sync_at: datetime | None
    day_start_utc: datetime
    day_end_utc: datetime
