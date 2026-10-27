from datetime import datetime

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.timeutil import utcnow
from app.db.base import Base
from app.models.enums import IncidentCategory, MatchType
from app.models.user import User


class DetectionRule(Base):
    __tablename__ = "detection_rules"
    __table_args__ = (
        UniqueConstraint("keyword_normalized", "match_type", name="uq_detection_rules_kw_match"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    keyword: Mapped[str] = mapped_column(String(200))
    keyword_normalized: Mapped[str] = mapped_column(String(200), index=True)
    category: Mapped[IncidentCategory] = mapped_column(
        Enum(IncidentCategory, native_enum=False, length=24)
    )
    match_type: Mapped[MatchType] = mapped_column(Enum(MatchType, native_enum=False, length=16))
    priority: Mapped[int] = mapped_column(Integer, default=50)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    created_by: Mapped[User | None] = relationship(foreign_keys=[created_by_user_id], lazy="joined")
    updated_by: Mapped[User | None] = relationship(foreign_keys=[updated_by_user_id], lazy="joined")

    @property
    def created_by_username(self) -> str | None:
        return self.created_by.username if self.created_by else None

    @property
    def updated_by_username(self) -> str | None:
        return self.updated_by.username if self.updated_by else None
