from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbDep, UserOrBotAuth
from app.models.enums import IncidentCategory
from app.schemas.common import Page
from app.schemas.rule import (
    ActiveRulesOut,
    RuleCreate,
    RuleOut,
    RulePatch,
    RulesVersionOut,
)
from app.services import rules_service, settings_service

router = APIRouter(prefix="/detection-rules", tags=["detection-rules"])


@router.get("", response_model=Page[RuleOut])
def list_rules(
    db: DbDep,
    _: CurrentUser,
    q: str | None = None,
    category: IncidentCategory | None = None,
    is_active: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Page[RuleOut]:
    items, total = rules_service.list_rules(
        db, q=q, category=category, is_active=is_active, page=page, page_size=page_size
    )
    return Page(items=items, total=total, page=page, page_size=page_size)


# Eslatma: "/active" va "/version" "/{id}" dan oldin e'lon qilinadi.
@router.get("/active", response_model=ActiveRulesOut, dependencies=[UserOrBotAuth])
def active(db: DbDep) -> ActiveRulesOut:
    return ActiveRulesOut(
        version=settings_service.get_rules_version(db), rules=rules_service.active_rules(db)
    )


@router.get("/version", response_model=RulesVersionOut, dependencies=[UserOrBotAuth])
def version(db: DbDep) -> RulesVersionOut:
    return RulesVersionOut(version=settings_service.get_rules_version(db))


@router.post("/rescan")
def rescan_rules(db: DbDep, _: CurrentUser) -> dict[str, int | str]:
    """Barcha faol qoidalar bo'yicha so'nggi 30 kunlik xabarlarni qayta tahlil qilib, yangi hodisalarni ochadi."""
    from app.services.channel_scraper import rescan_messages_with_rules
    rescanned = rescan_messages_with_rules(db)
    return {"status": "ok", "rescanned_incidents": rescanned}


@router.post("", response_model=RuleOut, status_code=201)
def create(data: RuleCreate, db: DbDep, user: CurrentUser) -> RuleOut:
    rule = rules_service.create_rule(db, data, user.id)
    from app.core.config import get_settings
    if get_settings().app_env != "test":
        try:
            from app.services.channel_scraper import rescan_messages_with_rules
            rescan_messages_with_rules(db)
        except Exception as e:
            import logging
            logging.getLogger("suvnazorat.rules").warning("Yangi qoida kiritilganda rescan xatosi: %s", e)
    return rule  # type: ignore[return-value]


@router.get("/{rule_id}", response_model=RuleOut)
def get(rule_id: int, db: DbDep, _: CurrentUser) -> RuleOut:
    return rules_service.get_rule(db, rule_id)  # type: ignore[return-value]


@router.patch("/{rule_id}", response_model=RuleOut)
def patch(rule_id: int, data: RulePatch, db: DbDep, user: CurrentUser) -> RuleOut:
    rule = rules_service.update_rule(db, rule_id, data, user.id)
    try:
        from app.services.channel_scraper import rescan_messages_with_rules
        rescan_messages_with_rules(db)
    except Exception as e:
        import logging
        logging.getLogger("suvnazorat.rules").warning("Qoida tahrirlanganda rescan xatosi: %s", e)
    return rule  # type: ignore[return-value]


@router.delete("/{rule_id}", status_code=204)
def delete(rule_id: int, db: DbDep, user: CurrentUser) -> None:
    rules_service.delete_rule(db, rule_id, user.id)

