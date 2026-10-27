"""Botdan kelgan xabarni qabul qilish: saqlash, qoidalar bo'yicha tahlil, hodisa yaratish/bog'lash.

Idempotentlik: (source_id, telegram_message_id) noyob. Takroriy so'rov yangi hodisa yaratmaydi.
"""
import logging
import re
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fastapi import HTTPException

from app.core.errors import AppError
from app.core.timeutil import utcnow
from app.models import (
    Incident,
    IncidentMessage,
    MonitoringSource,
    SourceMessage,
)
from app.models.enums import IncidentCategory, IncidentStatus, Priority, ProcessingStatus, SourceType
from app.schemas.bot import BotMessageIn, BotMessageOut
from app.services import rules_service
from app.services.address_extractor import extract_location
from app.services.ai_service import analyze_text_with_groq, get_heuristic_fallback
from app.services.matching import Analysis, analyze
from app.services.text import normalize_text

log = logging.getLogger("suvnazorat.ingest")

# O'xshash xabarlarni bitta hodisaga bog'lash chegarasi (ehtiyotkor: aniq bo'lmasa alohida hodisa).
GROUP_WINDOW = timedelta(hours=2)
GROUP_MIN_SIMILARITY = 0.6


_WORD = re.compile(r"[\w']+")


def _similarity(a: str, b: str) -> float:
    """So'zlar to'plamlari bo'yicha Jaccard; tinish belgilari hisobga olinmaydi."""
    sa = set(_WORD.findall(normalize_text(a)))
    sb = set(_WORD.findall(normalize_text(b)))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _find_related(
    db: Session, source_id: int, category: IncidentCategory, text: str, ts
) -> Incident | None:
    candidates = (
        db.scalars(
            select(Incident)
            .where(
                Incident.source_id == source_id,
                Incident.category == category,
                Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.IN_PROGRESS]),
                Incident.last_seen_at >= ts - GROUP_WINDOW,
            )
            .order_by(Incident.last_seen_at.desc())
            .limit(10)
        )
        .unique()
        .all()
    )
    for incident in candidates:
        if _similarity(incident.description, text) >= GROUP_MIN_SIMILARITY:
            return incident
    return None


def _find_related_by_resolution(db: Session, text: str, district: str | None, address: str | None) -> Incident | None:
    # 1. Telegram xabar havolasi bo'yicha moslik (masalan: https://t.me/kanal/123)
    link_match = re.search(r"https://t\.me/(?:c/\d+|[A-Za-z0-9_]+)/(\d+)", text)
    if link_match:
        try:
            tmid = int(link_match.group(1))
            msg_id = db.scalar(select(SourceMessage.id).where(SourceMessage.telegram_message_id == tmid))
            if msg_id:
                inc_id = db.scalar(select(IncidentMessage.incident_id).where(IncidentMessage.source_message_id == msg_id))
                if inc_id:
                    inc = db.get(Incident, inc_id)
                    if inc and inc.status in (IncidentStatus.OPEN, IncidentStatus.IN_PROGRESS):
                        return inc
        except (ValueError, TypeError):
            pass

    # 2. Manzil yoki Tuman bo'yicha ochiq zayavka bilan moslik
    if district or address:
        open_zayavkas = db.scalars(
            select(Incident).where(
                Incident.report_type.in_(["ZAYAVKA", "MUROJAAT"]),
                Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.IN_PROGRESS]),
            ).order_by(Incident.last_seen_at.desc()).limit(10)
        ).all()
        for inc in open_zayavkas:
            if district and inc.district and district.strip().lower() == inc.district.strip().lower():
                return inc
            if address and inc.address and (address.strip().lower() in inc.address.strip().lower() or inc.address.strip().lower() in address.strip().lower()):
                return inc
    return None


def _result(
    msg: SourceMessage,
    incident_id: int | None,
    duplicate: bool,
    flags: list[str],
    district: str | None = None,
    address: str | None = None,
):
    return BotMessageOut(
        status=msg.processing_status,
        duplicate=duplicate,
        message_id=msg.id,
        incident_id=incident_id,
        matched_rule_ids=list(msg.matched_rule_ids or []),
        flags=flags,
        district=district,
        address=address,
    )


def _existing_result(db: Session, existing: SourceMessage) -> BotMessageOut:
    link = db.scalar(
        select(IncidentMessage.incident_id).where(IncidentMessage.source_message_id == existing.id)
    )
    inc = db.get(Incident, link) if link else None
    return _result(
        existing,
        link,
        True,
        [],
        district=inc.district if inc else None,
        address=inc.address if inc else None,
    )


def _find_existing(db: Session, source_id: int, message_id: int) -> SourceMessage | None:
    return db.scalar(
        select(SourceMessage).where(
            SourceMessage.source_id == source_id,
            SourceMessage.telegram_message_id == message_id,
        )
    )


def _apply_analysis(
    db: Session,
    source: MonitoringSource,
    msg: SourceMessage,
    analysis: Analysis,
    is_citizen_report: bool = False,
) -> tuple[int | None, str | None, str | None]:
    district, address = extract_location(msg.message_text)

    if not analysis.has_match:
        if is_citizen_report:
            cat = IncidentCategory.OTHER
            prio = Priority.HIGH
        else:
            msg.processing_status = ProcessingStatus.NO_MATCH
            return None, district, address
    else:
        msg.matched_rule_ids = [r.id for r in analysis.matched]
        if analysis.review_required:
            msg.processing_status = ProcessingStatus.REVIEW_REQUIRED
            return None, district, address
        cat = analysis.category or IncidentCategory.OTHER
        prio = analysis.priority or Priority.MEDIUM

    ts = msg.telegram_timestamp
    # AI orqali xabar turini va xulosasini tahlil qilish (Groq / LLaMA / Heuristic)
    ai_res = analyze_text_with_groq(msg.message_text) or get_heuristic_fallback(msg.message_text)
    report_type = ai_res.get("report_type", "ZAYAVKA")
    ai_summary = ai_res.get("summary")

    # Telegram xabarida holat hal qilinganligi / bartaraf etilganligi ko'rsatilganmi?
    resolution_match = bool(re.search(
        r"\b(?:hal\s*qilindi|hal\s*qilingan|bartaraf\s*etildi|bartaraf\s*qilindi|ta['’‘]?mirlandi|tuzatildi|tozalandi|tiklandi|yechimini\s*topdi|chora\s*ko['’‘]?rildi|ҳал\s*қилинди|ҳал\s*қилинган|бартараф\s*этилди|бартараф\s*қилинди|таъмирланди|тузатилди|тозаланди|тикланди|чора\s*кўрилди|устранено|ликвидировано|решено|восстановлено)\b",
        msg.message_text,
        flags=re.IGNORECASE,
    )) or bool(ai_res.get("is_resolved"))

    if not address and ai_res.get("extracted_address"):
        address = ai_res.get("extracted_address")

    # Xabar turiga qarab mantiqiy status:
    # Yangiliklar, Minnatdorchilik va Rasmiy e'lonlar hech qachon OPEN (Hal qilinmagan) bo'lib turmaydi!
    if report_type in ("NEWS", "GRATITUDE", "ANNOUNCEMENT"):
        final_status = IncidentStatus.RESOLVED
    elif report_type == "IRRELEVANT":
        final_status = IncidentStatus.INVALID
    elif resolution_match:
        final_status = IncidentStatus.RESOLVED
    else:
        final_status = IncidentStatus.OPEN

    related = _find_related(db, source.id, cat, msg.message_text, ts)
    if related is None and resolution_match:
        related = _find_related_by_resolution(db, msg.message_text, district, address)
    if related is not None:
        related.last_seen_at = max(related.last_seen_at, ts)
        if not related.district and district:
            related.district = district
        if not related.address and address:
            related.address = address
        if not related.report_type:
            related.report_type = report_type
        if not related.ai_summary and ai_summary:
            related.ai_summary = ai_summary
        if final_status == IncidentStatus.RESOLVED:
            related.status = IncidentStatus.RESOLVED
            related.resolved_at = ts
            related.resolution_notes = f"Telegram xabari orqali holat bartaraf etilganligi ma'lum qilindi."
        existing_link = db.scalar(
            select(IncidentMessage.id).where(IncidentMessage.source_message_id == msg.id)
        )
        if not existing_link:
            db.add(IncidentMessage(incident_id=related.id, source_message_id=msg.id))
        msg.processing_status = ProcessingStatus.LINKED
        return related.id, related.district, related.address

    first_line = msg.message_text.strip().split("\n")[0]
    prefix = "Fuqaro murojaati: " if is_citizen_report else ""
    first_clean = " ".join(first_line.split())
    if is_citizen_report and "fuqaro:" in first_clean.lower():
        first_clean = re.sub(r"^[👤\s]*fuqaro:\s*", "", first_clean, flags=re.I).strip()

    if "gps" in msg.message_text.lower() or "maps.google.com" in msg.message_text.lower():
        loc_parts = [p for p in [district, address] if p and not p.startswith("GPS:")]
        if loc_parts:
            title = f"{prefix}Lokatsiya orqali murojaat ({', '.join(loc_parts)})"[:150]
        else:
            title = f"{prefix}GPS Lokatsiya orqali murojaat"
    else:
        title = f"{prefix}{first_clean[:110]}" or "Suv bilan bog'liq murojaat"

    incident = Incident(
        title=title,
        description=msg.message_text,
        category=cat,
        status=final_status,
        priority=prio,
        source_id=source.id,
        district=district,
        address=address,
        report_type=report_type,
        ai_summary=ai_summary,
        first_seen_at=ts,
        last_seen_at=ts,
        resolved_at=ts if final_status == IncidentStatus.RESOLVED else None,
        resolution_notes="Telegram xabarida muammo bartaraf etilganligi ko'rsatilgan." if final_status == IncidentStatus.RESOLVED else None,
    )
    db.add(incident)
    db.flush()
    existing_link = db.scalar(
        select(IncidentMessage.id).where(IncidentMessage.source_message_id == msg.id)
    )
    if not existing_link:
        db.add(IncidentMessage(incident_id=incident.id, source_message_id=msg.id))
    msg.processing_status = ProcessingStatus.INCIDENT_CREATED
    return incident.id, incident.district, incident.address


def ingest_message(db: Session, data: BotMessageIn) -> BotMessageOut:
    if data.is_citizen_report:
        from app.services.source_service import get_or_create_bot_source
        source = get_or_create_bot_source(db)
        # Turli fuqarolar shaxsiy chatidan bir xil message_id kelishi mumkinligi sababli chat_id bilan unikal qilamiz
        unique_message_id = abs(data.chat_id) * 1000000 + (data.message_id % 1000000)
    else:
        source = db.scalar(
            select(MonitoringSource).where(MonitoringSource.telegram_chat_id == data.chat_id)
        )
        if source is None and data.chat_username:
            source = db.scalar(
                select(MonitoringSource).where(MonitoringSource.telegram_username == data.chat_username)
            )
        if source is None or not source.is_active:
            raise HTTPException(404, "source_not_registered")
        unique_message_id = data.message_id

    existing = _find_existing(db, source.id, unique_message_id)
    if existing is not None:
        return _existing_result(db, existing)

    message_text = data.text
    if data.sender_phone and data.sender_phone not in message_text:
        message_text = f"{message_text}\n📞 Fuqaro telefoni: {data.sender_phone}"
    if data.sender_name and data.sender_name not in message_text:
        message_text = f"👤 Fuqaro: {data.sender_name}\n{message_text}"

    msg = SourceMessage(
        source_id=source.id,
        telegram_message_id=unique_message_id,
        message_text=message_text,
        message_url=data.message_url,
        media_type=data.media_type,
        telegram_file_id=data.file_id,
        telegram_timestamp=data.timestamp,
        received_at=utcnow(),
    )

    db.add(msg)
    try:
        db.flush()
    except IntegrityError:
        # Parallel takroriy so'rov: ikkinchisi yutqazdi — mavjud natijani qaytaramiz.
        db.rollback()
        source = db.scalar(
            select(MonitoringSource).where(MonitoringSource.telegram_chat_id == data.chat_id)
        )
        assert source is not None
        existing = _find_existing(db, source.id, data.message_id)
        if existing is None:
            raise
        return _existing_result(db, existing)

    analysis = analyze(data.text, rules_service.active_rules(db))
    incident_id, district, address = _apply_analysis(
        db, source, msg, analysis, is_citizen_report=data.is_citizen_report
    )

    source.last_received_at = utcnow()
    if source.last_message_at is None or data.timestamp > source.last_message_at:
        source.last_message_at = data.timestamp
    db.commit()
    log.info(
        "message processed source=%s status=%s incident=%s",
        source.id, msg.processing_status.value, incident_id,
    )
    return _result(msg, incident_id, False, analysis.flags, district=district, address=address)
