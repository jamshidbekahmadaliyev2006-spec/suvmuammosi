from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.models.enums import IncidentCategory, MatchType
from app.schemas.common import Str120

Keyword = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=200)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]


class RuleCreate(BaseModel):
    name: Str120
    keyword: Keyword
    category: IncidentCategory
    match_type: MatchType = MatchType.PHRASE
    priority: int = Field(default=50, ge=1, le=100)
    description: Description | None = None
    is_active: bool = True


class RulePatch(BaseModel):
    name: Str120 | None = None
    keyword: Keyword | None = None
    category: IncidentCategory | None = None
    match_type: MatchType | None = None
    priority: int | None = Field(default=None, ge=1, le=100)
    description: Description | None = None
    is_active: bool | None = None


class RuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    keyword: str
    category: IncidentCategory
    match_type: MatchType
    priority: int
    is_active: bool
    description: str | None
    created_at: datetime
    updated_at: datetime
    created_by_username: str | None
    updated_by_username: str | None


class ActiveRuleOut(BaseModel):
    """Botga beriladigan minimal ko'rinish."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    keyword: str
    category: IncidentCategory
    match_type: MatchType
    priority: int


class ActiveRulesOut(BaseModel):
    version: int
    rules: list[ActiveRuleOut]


class RulesVersionOut(BaseModel):
    version: int
