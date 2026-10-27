from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_action(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Audit yozuvi. details ichiga parol/token kabi maxfiy qiymat qo'yilmaydi."""
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=None if entity_id is None else str(entity_id),
            details=details or {},
        )
    )
