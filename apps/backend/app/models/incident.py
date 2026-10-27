from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.timeutil import utcnow
from app.db.base import Base
from app.models.enums import IncidentCategory, IncidentStatus, Priority, SourceType
from app.models.source import MonitoringSource, SourceMessage
from app.models.user import User


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (Index("ix_incidents_status_first_seen", "status", "first_seen_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[IncidentCategory] = mapped_column(
        Enum(IncidentCategory, native_enum=False, length=24), index=True
    )
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus, native_enum=False, length=16), default=IncidentStatus.OPEN
    )
    priority: Mapped[Priority] = mapped_column(Enum(Priority, native_enum=False, length=8))
    # Asosiy manba (spetsifikatsiyaga qo'shimcha ustun: ro'yxat va guruhlash tezligi uchun).
    source_id: Mapped[int] = mapped_column(
        ForeignKey("monitoring_sources.id", ondelete="RESTRICT"), index=True
    )
    district: Mapped[str | None] = mapped_column(String(120))  # faqat ishonchli bo'lsa
    address: Mapped[str | None] = mapped_column(String(300))  # faqat ishonchli bo'lsa
    first_seen_at: Mapped[datetime]
    last_seen_at: Mapped[datetime]
    resolved_at: Mapped[datetime | None]
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    report_type: Mapped[str | None] = mapped_column(String(50), default="MUROJAAT")
    ai_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    source: Mapped[MonitoringSource] = relationship(lazy="joined")
    incident_messages: Mapped[list["IncidentMessage"]] = relationship(
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def source_name(self) -> str:
        return self.source.name if self.source else "Noma'lum manba"

    @property
    def source_type(self) -> str:
        return self.source.source_type.value if self.source else "GROUP"

    @property
    def source_username(self) -> str | None:
        return self.source.telegram_username if self.source else None

    @property
    def message_url(self) -> str | None:
        import re
        msg_id = None
        if self.incident_messages:
            for im in self.incident_messages:
                if im.source_message:
                    msg_id = im.source_message.telegram_message_id
                    if im.source_message.message_url:
                        url = im.source_message.message_url
                        # Agar url oxirida message_id bo'lmasa, uni qo'shib to'g'ridan-to'g'ri xabarga olib boramiz
                        if msg_id and not re.search(r"/\d+$", url):
                            url = f"{url.rstrip('/')}/{msg_id}"
                        return url

        # Tavsifda (description) to'g'ridan-to'g'ri xabar havolasi bo'lsa
        if self.description:
            m = re.search(r"https://t\.me/(?:c/\d+|\w+)(?:/\d+)+", self.description)
            if m:
                return m.group(0)

        if self.source:
            # Agar bot bo'lsa, xabarga emas botga yo'naltiriladi
            if self.source.source_type == SourceType.BOT:
                return f"https://t.me/{self.source.telegram_username or 'hokimyatsuvnazorati_bot'}"
            if self.source.telegram_username:
                base = f"https://t.me/{self.source.telegram_username}"
                return f"{base}/{msg_id}" if msg_id else base
            if self.source.telegram_chat_id:
                chat_str = str(self.source.telegram_chat_id)
                cid = chat_str[4:] if chat_str.startswith("-100") else chat_str.lstrip("-")
                base = f"https://t.me/c/{cid}"
                return f"{base}/{msg_id}" if msg_id else base
        return None

    @property
    def media_type(self) -> str | None:
        if self.incident_messages:
            for im in self.incident_messages:
                if im.source_message and im.source_message.media_type:
                    return im.source_message.media_type
        return None

    @property
    def file_id(self) -> str | None:
        if self.incident_messages:
            for im in self.incident_messages:
                if im.source_message and im.source_message.telegram_file_id:
                    return im.source_message.telegram_file_id
        return None

    @property
    def media_url(self) -> str | None:
        fid = self.file_id
        if fid and self.media_type in ("photo", "document"):
            return f"/api/v1/system/media/{fid}"
        return None

    @property
    def location_url(self) -> str | None:
        fid = self.file_id
        if self.media_type == "location" and fid and "," in fid:
            parts = fid.split(",")
            return f"https://maps.google.com/?q={parts[0].strip()},{parts[1].strip()}"
        desc = self.description or ""
        if "maps.google.com" in desc:
            import re
            m = re.search(r"https?://maps\.google\.com[^\s]+", desc)
            if m:
                return m.group(0)
        return None

    @property
    def matched_rule_ids(self) -> list[int]:
        ids: list[int] = []
        if self.incident_messages:
            for im in self.incident_messages:
                if im.source_message and im.source_message.matched_rule_ids:
                    for rid in im.source_message.matched_rule_ids:
                        if rid not in ids:
                            ids.append(rid)
        return ids


class IncidentMessage(Base):
    __tablename__ = "incident_messages"
    __table_args__ = (
        # Bir xabar faqat bitta hodisaga bog'lanadi.
        UniqueConstraint("source_message_id", name="uq_incident_messages_source_message"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id", ondelete="RESTRICT"), index=True
    )
    source_message_id: Mapped[int] = mapped_column(
        ForeignKey("source_messages.id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    source_message: Mapped[SourceMessage] = relationship(lazy="joined")


class IncidentStatusHistory(Base):
    __tablename__ = "incident_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id", ondelete="RESTRICT"), index=True
    )
    old_status: Mapped[IncidentStatus | None] = mapped_column(
        Enum(IncidentStatus, native_enum=False, length=16)
    )
    new_status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus, native_enum=False, length=16)
    )
    changed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    changed_by: Mapped[User | None] = relationship(lazy="joined")

    @property
    def changed_by_username(self) -> str | None:
        return self.changed_by.username if self.changed_by else None


class IncidentComment(Base):
    __tablename__ = "incident_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id", ondelete="RESTRICT"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    user: Mapped[User] = relationship(lazy="joined")

    @property
    def username(self) -> str:
        return self.user.username
