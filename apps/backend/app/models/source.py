from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.timeutil import utcnow
from app.db.base import Base
from app.models.enums import ProcessingStatus, SourceType


class MonitoringSource(Base):
    __tablename__ = "monitoring_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    telegram_username: Mapped[str | None] = mapped_column(String(64))
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType, native_enum=False, length=16))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_message_at: Mapped[datetime | None]
    last_received_at: Mapped[datetime | None]  # oxirgi muvaffaqiyatli qabul qilish
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)


class SourceMessage(Base):
    __tablename__ = "source_messages"
    __table_args__ = (
        UniqueConstraint("source_id", "telegram_message_id", name="uq_source_messages_source_msg"),
        Index("ix_source_messages_received_at", "received_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("monitoring_sources.id", ondelete="RESTRICT"))
    telegram_message_id: Mapped[int] = mapped_column(BigInteger)
    message_text: Mapped[str] = mapped_column(Text)  # asl matn, o'zgartirilmaydi
    message_url: Mapped[str | None] = mapped_column(String(500))
    media_type: Mapped[str | None] = mapped_column(String(32))
    telegram_file_id: Mapped[str | None] = mapped_column(String(255))
    telegram_timestamp: Mapped[datetime]
    received_at: Mapped[datetime] = mapped_column(default=utcnow)
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, native_enum=False, length=24), default=ProcessingStatus.RECEIVED
    )
    matched_rule_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    source: Mapped[MonitoringSource] = relationship(lazy="joined")

    @property
    def source_name(self) -> str:
        return self.source.name
