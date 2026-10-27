from typing import Any

from sqlalchemy.orm import Session

from app.models import SystemSetting

RULES_VERSION = "rules_version"
BOT_HEARTBEAT = "bot_heartbeat"
ADMIN_PHONES = "admin_phones"


def get_setting(db: Session, key: str) -> dict[str, Any] | None:
    row = db.get(SystemSetting, key)
    if row is None:
        return None
    if isinstance(row.value, dict):
        return dict(row.value)
    if isinstance(row.value, (int, float, str, bool)):
        return {"v": row.value}
    try:
        return dict(row.value)
    except Exception:
        return {"v": row.value}


def set_setting(db: Session, key: str, value: dict[str, Any]) -> None:
    row = db.get(SystemSetting, key)
    if row is None:
        db.merge(SystemSetting(key=key, value=value))
    else:
        row.value = value


def get_rules_version(db: Session) -> int:
    row = db.get(SystemSetting, RULES_VERSION)
    if row is None:
        return 0
    if isinstance(row.value, int):
        return row.value
    if isinstance(row.value, dict):
        return int(row.value.get("v", 0))
    try:
        return int(row.value)
    except (ValueError, TypeError):
        return 0


def bump_rules_version(db: Session) -> int:
    """Har bir qoida o'zgarishida oshiriladi — bot shu raqam orqali yangilanishni bilib oladi."""
    new = get_rules_version(db) + 1
    set_setting(db, RULES_VERSION, {"v": new})
    return new


def get_admin_phones(db: Session) -> list[str]:
    data = get_setting(db, ADMIN_PHONES)
    if data and "phones" in data and isinstance(data["phones"], list):
        return [str(p).strip() for p in data["phones"] if str(p).strip()]
    return []


def set_admin_phones(db: Session, phones: list[str]) -> list[str]:
    clean = [str(p).strip() for p in phones if str(p).strip()]
    set_setting(db, ADMIN_PHONES, {"phones": clean})
    return clean


def is_admin_phone(db: Session, phone: str) -> bool:
    if not phone:
        return False
    target = "".join(ch for ch in phone if ch.isdigit())
    if not target:
        return False
    for p in get_admin_phones(db):
        p_clean = "".join(ch for ch in p if ch.isdigit())
        if p_clean and (p_clean == target or target.endswith(p_clean) or p_clean.endswith(target)):
            return True
    return False
