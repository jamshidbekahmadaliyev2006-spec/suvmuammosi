from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import DetectionRule
from app.models.enums import IncidentCategory, MatchType
from app.schemas.rule import RuleCreate, RulePatch
from app.services import audit, settings_service
from app.services.text import like_pattern, normalize_text


def _normalized_or_error(keyword: str) -> str:
    norm = normalize_text(keyword)
    if len(norm) < 2:
        raise AppError(422, "invalid_keyword", "Kalit so'z kamida 2 ta belgidan iborat bo'lsin.")
    return norm


def _ensure_unique(db: Session, norm: str, match_type: MatchType, exclude_id: int | None) -> None:
    stmt = select(DetectionRule.id).where(
        DetectionRule.keyword_normalized == norm, DetectionRule.match_type == match_type
    )
    if exclude_id is not None:
        stmt = stmt.where(DetectionRule.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise AppError(409, "rule_exists", "Bunday kalit so'z va moslik turi allaqachon mavjud.")


def get_rule(db: Session, rule_id: int) -> DetectionRule:
    rule = db.get(DetectionRule, rule_id)
    if rule is None:
        raise AppError(404, "rule_not_found", "Qoida topilmadi.")
    return rule


def create_rule(db: Session, data: RuleCreate, user_id: int | None) -> DetectionRule:
    norm = _normalized_or_error(data.keyword)
    _ensure_unique(db, norm, data.match_type, None)
    rule = DetectionRule(
        **data.model_dump(),
        keyword_normalized=norm,
        created_by_user_id=user_id,
        updated_by_user_id=user_id,
    )
    db.add(rule)
    db.flush()
    settings_service.bump_rules_version(db)
    audit.log_action(
        db, user_id=user_id, action="rule.create", entity_type="detection_rule",
        entity_id=rule.id, details={"keyword": rule.keyword, "is_active": rule.is_active},
    )
    db.commit()
    db.refresh(rule)
    return rule


def update_rule(db: Session, rule_id: int, data: RulePatch, user_id: int) -> DetectionRule:
    rule = get_rule(db, rule_id)
    changes = data.model_dump(exclude_unset=True)
    for key, value in changes.items():
        if value is None and key != "description":
            continue  # NOT NULL maydonlarga null yozilmaydi
        setattr(rule, key, value)
    if "keyword" in changes or "match_type" in changes:
        rule.keyword_normalized = _normalized_or_error(rule.keyword)
        _ensure_unique(db, rule.keyword_normalized, rule.match_type, rule.id)
    rule.updated_by_user_id = user_id
    settings_service.bump_rules_version(db)
    action = "rule.update"
    if changes.get("is_active") is False:
        action = "rule.deactivate"
    elif changes.get("is_active") is True:
        action = "rule.activate"
    audit.log_action(
        db, user_id=user_id, action=action, entity_type="detection_rule",
        entity_id=rule.id, details={"fields": sorted(changes)},
    )
    db.commit()
    db.refresh(rule)
    return rule


def list_rules(
    db: Session, *, q: str | None, category: IncidentCategory | None,
    is_active: bool | None, page: int, page_size: int,
) -> tuple[list[DetectionRule], int]:
    stmt = select(DetectionRule)
    if q:
        like = like_pattern(q)
        stmt = stmt.where(
            or_(
                DetectionRule.keyword.ilike(like, escape="\\"),
                DetectionRule.name.ilike(like, escape="\\"),
            )
        )
    if category:
        stmt = stmt.where(DetectionRule.category == category)
    if is_active is not None:
        stmt = stmt.where(DetectionRule.is_active == is_active)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    # Guruh va kanallar kabi eng oxirgi qo'shilgan kalit so'zlar birinchi chiqadi (newest first)
    stmt = stmt.order_by(DetectionRule.id.desc())
    items = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).unique().all()
    return list(items), total


def active_rules(db: Session) -> list[DetectionRule]:
    return list(
        db.scalars(select(DetectionRule).where(DetectionRule.is_active.is_(True))).unique().all()
    )


get_active_rules = active_rules


def delete_rule(db: Session, rule_id: int, user_id: int) -> None:
    rule = get_rule(db, rule_id)
    keyword = rule.keyword
    db.delete(rule)
    settings_service.bump_rules_version(db)
    audit.log_action(
        db,
        user_id=user_id,
        action="rule.delete",
        entity_type="detection_rule",
        entity_id=rule_id,
        details={"keyword": keyword},
    )
    db.commit()

