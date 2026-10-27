from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.models.enums import IncidentCategory, IncidentStatus, Priority, ProcessingStatus

Note = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    source_name: str
    telegram_message_id: int
    message_text: str
    message_url: str | None
    telegram_timestamp: datetime
    received_at: datetime
    processing_status: ProcessingStatus
    matched_rule_ids: list[int]


class IncidentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    category: IncidentCategory
    status: IncidentStatus
    priority: Priority
    source_id: int
    source_name: str
    source_type: str | None = None
    source_username: str | None = None
    message_url: str | None = None
    district: str | None
    address: str | None
    media_type: str | None = None
    file_id: str | None = None
    media_url: str | None = None
    location_url: str | None = None
    first_seen_at: datetime
    last_seen_at: datetime
    matched_rule_ids: list[int] = []
    report_type: str | None = "MUROJAAT"
    ai_summary: str | None = None
    resolution_notes: str | None = None
    resolved_at: datetime | None = None


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    username: str
    comment: str
    created_at: datetime


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    old_status: IncidentStatus | None
    new_status: IncidentStatus
    changed_by_user_id: int | None
    changed_by_username: str | None
    comment: str | None
    created_at: datetime


class IncidentDetail(IncidentListItem):
    description: str
    resolution_notes: str | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime
    first_message: MessageOut | None
    comments: list[CommentOut]


class IncidentPatch(BaseModel):
    status: IncidentStatus | None = None
    priority: Priority | None = None
    category: IncidentCategory | None = None
    resolution_notes: Note | None = None
    district: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None = None
    address: Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)] | None = None
    comment: Note | None = None  # status tarixiga yoziladigan izoh


class CommentIn(BaseModel):
    comment: Note
