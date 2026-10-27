from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.models.enums import ProcessingStatus, SourceType


class BotMessageIn(BaseModel):
    chat_id: int
    message_id: int
    chat_title: Annotated[str, StringConstraints(max_length=200)] | None = None
    chat_username: Annotated[str, StringConstraints(max_length=64)] | None = None
    chat_type: SourceType | None = None
    text: Annotated[str, StringConstraints(max_length=20000)] = ""
    timestamp: datetime
    message_url: Annotated[str, StringConstraints(max_length=500)] | None = None
    media_type: Annotated[str, StringConstraints(max_length=32)] | None = None
    file_id: Annotated[str, StringConstraints(max_length=255)] | None = None
    is_citizen_report: bool = False
    sender_phone: str | None = None
    sender_name: str | None = None



class BotMessageOut(BaseModel):
    status: ProcessingStatus
    duplicate: bool
    message_id: int
    incident_id: int | None
    matched_rule_ids: list[int]
    flags: list[str]
    district: str | None = None
    address: str | None = None


class HeartbeatIn(BaseModel):
    bot_version: Annotated[str, StringConstraints(max_length=32)] | None = None
    rules_version: int | None = None
    rules_loaded: bool = False
    rules_fetched_at: datetime | None = None
    watched_sources: int | None = Field(default=None, ge=0)


class BotSourceRegisterIn(BaseModel):
    chat_id: int
    chat_title: Annotated[str, StringConstraints(max_length=200)]
    chat_username: Annotated[str, StringConstraints(max_length=64)] | None = None
    source_type: SourceType = SourceType.GROUP


class BotCancelIncidentIn(BaseModel):
    incident_id: int
    chat_id: int

