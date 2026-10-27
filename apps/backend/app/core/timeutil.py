"""Vaqt yordamchilari: bazada hamma narsa UTC, kun chegaralari APP_TIMEZONE bo'yicha."""
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def utcnow() -> datetime:
    return datetime.now(UTC)


def local_day_bounds_utc(day: date) -> tuple[datetime, datetime]:
    """Mahalliy kunning [boshlanishi, keyingi kun boshlanishi) oralig'i — UTC da."""
    tz = ZoneInfo(get_settings().app_timezone)
    start = datetime(day.year, day.month, day.day, tzinfo=tz)
    end = datetime(day.year, day.month, day.day, tzinfo=tz) + timedelta(days=1)
    return start.astimezone(UTC), end.astimezone(UTC)


def today_bounds_utc(now: datetime | None = None) -> tuple[datetime, datetime]:
    tz = ZoneInfo(get_settings().app_timezone)
    local_today = (now or utcnow()).astimezone(tz).date()
    return local_day_bounds_utc(local_today)
