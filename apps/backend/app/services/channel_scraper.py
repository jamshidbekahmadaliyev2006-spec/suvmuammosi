import html as html_lib
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import IncidentMessage, MonitoringSource, SourceMessage
from app.models.enums import ProcessingStatus, SourceType
from app.schemas.bot import BotMessageIn
from app.services import ingest_service, rules_service
from app.services.matching import analyze

log = logging.getLogger("suvnazorat.scraper")


def fetch_public_channel_posts(
    username: str, days_back: int = 10, max_pages: int = 15
) -> list[dict[str, Any]]:
    """Ochiq Telegram kanalining web-preview (https://t.me/s/{username}) dan postlarni oladi.
    Agar days_back berilgan bo'lsa, ?before={id} orqali oxirgi N kunlik barcha postlarni qidirib topadi.
    """
    clean_user = username.lstrip("@").strip()
    if not clean_user:
        return []

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    all_posts: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    current_url = f"https://t.me/s/{clean_user}"

    try:
        with httpx.Client(timeout=12.0, follow_redirects=True) as client:
            for page in range(max_pages):
                resp = client.get(current_url, headers=headers)
                if resp.status_code != 200:
                    break
                content = resp.text

                chunks = re.findall(
                    r'<div class="[^"]*tgme_widget_message\b[^"]*"[^>]*data-post="([^"]+)"[^>]*>([\s\S]*?)<div class="tgme_widget_message_footer',
                    content,
                )
                if not chunks:
                    break

                page_posts: list[dict[str, Any]] = []
                earliest_msg_id: int | None = None
                earliest_date: datetime | None = None

                for post_id, chunk in chunks:
                    parts = post_id.split("/")
                    msg_id = (
                        int(parts[-1])
                        if len(parts) > 1 and parts[-1].isdigit()
                        else abs(hash(post_id)) % 1000000
                    )
                    if msg_id in seen_ids:
                        continue
                    seen_ids.add(msg_id)

                    text_match = re.search(
                        r'<div class="[^"]*tgme_widget_message_text[^"]*"[^>]*>([\s\S]*?)</div>',
                        chunk,
                    )
                    if not text_match:
                        continue

                    raw_html = text_match.group(1)
                    clean_text = re.sub(r"<br\s*/?>", "\n", raw_html)
                    clean_text = re.sub(r"<[^>]+>", " ", clean_text)
                    clean_text = html_lib.unescape(clean_text).strip()
                    if not clean_text:
                        continue

                    time_match = re.search(r'<time datetime="([^"]+)"', chunk)
                    if time_match:
                        try:
                            dt = datetime.fromisoformat(
                                time_match.group(1).replace("Z", "+00:00")
                            )
                        except Exception:
                            dt = datetime.now(timezone.utc)
                    else:
                        dt = datetime.now(timezone.utc)

                    if earliest_date is None or dt < earliest_date:
                        earliest_date = dt
                        earliest_msg_id = msg_id

                    page_posts.append({
                        "message_id": msg_id,
                        "text": clean_text,
                        "timestamp": dt,
                        "message_url": f"https://t.me/{post_id}",
                    })

                all_posts.extend(page_posts)

                # Agar olingan eng eski xabar 10 kundan oldingi bo'lsa, to'xtatamiz
                if earliest_date and earliest_date < cutoff_date:
                    break

                # Agar oldingi xabar ID si topilsa, ?before={id} orqali sahifalash
                if earliest_msg_id and len(chunks) >= 15:
                    current_url = f"https://t.me/s/{clean_user}?before={earliest_msg_id}"
                else:
                    break
    except Exception as e:
        log.warning("Telegram kanal postlarini olishda xatolik (@%s): %s", clean_user, e)

    return all_posts


def sync_source_channel_posts(
    db: Session, source: MonitoringSource, days_back: int = 10
) -> int:
    """Bitta manba uchun postlarni olib, bazaga va tahlil tizimiga (ingest) uzatadi."""
    if not source.telegram_username or not source.is_active:
        return 0

    posts = fetch_public_channel_posts(source.telegram_username, days_back=days_back)
    ingested_count = 0
    for p in posts:
        try:
            data = BotMessageIn(
                chat_id=source.telegram_chat_id,
                message_id=p["message_id"],
                chat_title=source.name,
                chat_username=source.telegram_username,
                chat_type=source.source_type,
                text=p["text"],
                timestamp=p["timestamp"],
                message_url=p["message_url"],
                is_citizen_report=False,
            )
            ingest_service.ingest_message(db, data)
            ingested_count += 1
        except Exception as e:
            log.debug("Postni saqlashda xatolik (msg_id=%s): %s", p["message_id"], e)

    return ingested_count


def sync_all_active_channels(db: Session, days_back: int = 1) -> dict[str, int]:
    """Barcha faol kanallarni aylanib chiqib, yangi postlarni tekshiradi."""
    sources = db.scalars(
        select(MonitoringSource).where(
            MonitoringSource.is_active == True,
            MonitoringSource.telegram_username.isnot(None),
        )
    ).all()
    results = {}
    for src in sources:
        cnt = sync_source_channel_posts(db, src, days_back=days_back)
        results[src.name] = cnt
    return results


def rescan_messages_with_rules(db: Session) -> int:
    """Yangi yoki yangilangan qoidalar bo'yicha bazadagi mavjud xabarlarni qayta tahlil qiladi.
    Agar ilgari mos kelmagan xabar endi yangi kalit so'zga mos kelsa, avtomatik ravishda yangi hodisa ochiladi!
    """
    from datetime import timedelta
    from app.core.timeutil import utcnow
    from app.services.ingest_service import _apply_analysis

    rules = rules_service.active_rules(db)
    if not rules:
        return 0

    # So'nggi 30 kunlik mos kelmagan va hali hodisaga biriktirilmagan xabarlarni qidiramiz
    since = utcnow() - timedelta(days=30)
    messages = db.scalars(
        select(SourceMessage)
        .where(
            SourceMessage.received_at >= since,
            SourceMessage.processing_status.in_([ProcessingStatus.NO_MATCH, ProcessingStatus.REVIEW_REQUIRED]),
            ~SourceMessage.id.in_(select(IncidentMessage.source_message_id)),
        )
        .order_by(SourceMessage.id.asc())
    ).all()

    created_or_linked = 0
    for msg in messages:
        analysis = analyze(msg.message_text, rules)
        if analysis.has_match and not analysis.review_required:
            source = db.get(MonitoringSource, msg.source_id)
            if source:
                inc_id, dist, addr = _apply_analysis(db, source, msg, analysis, is_citizen_report=False)
                if inc_id:
                    created_or_linked += 1

    if created_or_linked > 0:
        db.commit()
    log.info("rescan_messages_with_rules: %d ta xabar yangi hodisalarga aylantirildi", created_or_linked)
    return created_or_linked
