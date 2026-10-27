from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.enums import SourceType


class SourceResolveIn(BaseModel):
    identifier: str


class SourceResolveOut(BaseModel):
    telegram_chat_id: int
    name: str
    telegram_username: str
    source_type: SourceType
    resolved: bool


class SourceCreate(BaseModel):
    name: str | None = None
    telegram_chat_id: int | None = None
    telegram_username: str | None = None
    source_type: SourceType = SourceType.CHANNEL
    is_active: bool = True


class SourcePatch(BaseModel):
    name: str | None = None
    telegram_chat_id: int | None = None
    telegram_username: str | None = None
    source_type: SourceType | None = None
    is_active: bool | None = None


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    telegram_chat_id: int
    telegram_username: str | None
    source_type: SourceType
    is_active: bool
    last_message_at: datetime | None
    last_received_at: datetime | None
    created_at: datetime


class SyncHistoryIn(BaseModel):
    days_back: int = 10


class SyncHistoryOut(BaseModel):
    status: str
    synced_sources: int
    total_messages_synced: int
    rescanned_incidents: int
