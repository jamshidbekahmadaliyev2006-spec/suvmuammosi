"""Qoidalar bo'yicha moslikni aniqlash va kontekst (inkor / hal bo'lgan / rejali) tahlili.

Muhim: oddiy kalit so'z moslik kontekstni to'liq tushunmaydi. Shuning uchun inkor yoki
hal bo'lgan xabarlar avtomatik faol avariya qilinmaydi — REVIEW_REQUIRED bo'lib,
foydalanuvchi tekshiruviga qoldiriladi.
"""
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Protocol

from app.models.enums import IncidentCategory, MatchType, Priority
from app.services.text import STOP_WORDS, extract_key_tokens, normalize_text, to_canonical_concept


class RuleLike(Protocol):
    id: int
    keyword_normalized: str
    match_type: MatchType
    category: IncidentCategory
    priority: int


_BOUNDARY_BEFORE = r"(?<![\w'])"
_BOUNDARY_AFTER = r"(?![\w'])"
_CONNECTOR = r"(?:[^\w']+(?:[\w']{1,15}[^\w']+)?|[^\w']+)"


@lru_cache(maxsize=2048)
def build_pattern(normalized_keyword: str, match_type: MatchType) -> re.Pattern[str]:
    """Foydalanuvchi regex kiritmaydi — xavfsiz moslik patterni yaratadi."""
    if match_type == MatchType.CONTAINS:
        return re.compile(re.escape(normalized_keyword))
    if match_type == MatchType.WHOLE_WORD:
        return re.compile(_BOUNDARY_BEFORE + re.escape(normalized_keyword) + _BOUNDARY_AFTER)
    tokens = [t for t in re.split(r"[^\w']+", normalized_keyword) if t]
    if len(tokens) == 2:
        p1 = re.escape(tokens[0]) + _CONNECTOR + re.escape(tokens[1])
        p2 = re.escape(tokens[1]) + _CONNECTOR + re.escape(tokens[0])
        body = f"(?:{p1}|{p2})"
    else:
        body = _CONNECTOR.join(re.escape(t) for t in tokens)
    return re.compile(_BOUNDARY_BEFORE + body + _BOUNDARY_AFTER)


@lru_cache(maxsize=4096)
def get_rule_patterns(keyword_normalized: str, match_type: MatchType) -> list[re.Pattern[str]]:
    """To'g'ridan-to'g'ri va ko'p tilli (rus, lotin, kirill, ingliz) semantik qoliplarni tuzadi."""
    direct_pat = build_pattern(keyword_normalized, match_type)
    patterns = [direct_pat]

    # Semantik tushunchalar qolipi (ko'p tilli va harf registridan qat'iy nazar moslik)
    if match_type != MatchType.CONTAINS:
        concept_kw = to_canonical_concept(keyword_normalized)
        key_tokens = extract_key_tokens(concept_kw)
        raw_words = [t for t in re.split(r"[^\w']+", keyword_normalized) if t and t not in STOP_WORDS]
        if key_tokens:
            if len(key_tokens) == 1:
                # Bitta so'zli kalit faqat aslida ham bitta so'z bo'lsagina mos deb olinadi
                if len(raw_words) <= 1:
                    patterns.append(re.compile(_BOUNDARY_BEFORE + re.escape(key_tokens[0]) + _BOUNDARY_AFTER))
            elif len(key_tokens) == 2:
                # Ikki so'zli juftlik (masalan: yomg'ir suvi, yong'in chiqqan) YONMA-YON kelishi shart!
                cp1 = re.escape(key_tokens[0]) + _CONNECTOR + re.escape(key_tokens[1])
                cp2 = re.escape(key_tokens[1]) + _CONNECTOR + re.escape(key_tokens[0])
                patterns.append(re.compile(_BOUNDARY_BEFORE + f"(?:{cp1}|{cp2})" + _BOUNDARY_AFTER))
            else:
                # Ko'p so'zli iboralar to'liq yonma-yon kelishi shart
                body = _CONNECTOR.join(re.escape(t) for t in key_tokens)
                patterns.append(re.compile(_BOUNDARY_BEFORE + body + _BOUNDARY_AFTER))

    return patterns


def rule_matches(normalized_text: str, concept_text: str, rule: RuleLike) -> bool:
    """Xabar matnini qoida bilan to'g'ridan-to'g'ri va ko'p tilli qoliplar bo'yicha tekshiradi."""
    patterns = get_rule_patterns(rule.keyword_normalized, rule.match_type)
    if patterns[0].search(normalized_text) is not None:
        return True

    # Agar to'g'ridan-to'g'ri mos kelmasa, semantik tushunchalar bo'yicha tekshirish
    if len(patterns) > 1:
        for pat in patterns[1:]:
            if pat.search(concept_text) is not None:
                return True
    return False


# Kontekst belgilari (O'zbekcha, Ruscha, Inglizcha)
_NEGATION = re.compile(
    r"(muammo|muammosi|avariya|avariyasi|nosozlik)\s+(yo'q|yoq|emas|kuzatilmadi|bo'lmadi)"
    r"|hech qanday\s+(muammo|avariya)|muammo\s+bartaraf"
    r"|нет\s+(проблем|аварий|утечек|претензий)|проблем\s+нет"
    r"|no\s+(problem|issue|trouble|damage)"
)
_RESOLVED = re.compile(
    r"tiklandi|tiklangan|tuzatildi|bartaraf\s+etildi|hal\s+(bo'ldi|qilindi)"
    r"|ta'mirlab\s+bo'lindi|ta'mirlandi|yo'qotildi"
    r"|починили|исправили|устранили|ликвидировали|восстановили|включили\s+воду|дали\s+воду"
    r"|fixed|repaired|resolved|restored|back\s+on"
)
_PLANNED = re.compile(
    r"\b(ertaga|ertadan|indinga|rejali|rejalashtirilgan|reja\s+asosida)\b"
    r"|\b(ta'mirlanadi|o'chiriladi|to'xtatiladi|o'chirilishi)\b|\bvaqtincha\b"
    r"|\b(завтра|плановый|плановые|планового|плановое|плановые\s+работы|временно|будет\s+отключена)\b"
    r"|\b(tomorrow|planned|scheduled|maintenance|temporary|will\s+be\s+shut)\b"
)


@dataclass
class Analysis:
    matched: list[RuleLike] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    review_required: bool = False
    category: IncidentCategory | None = None
    priority: Priority = Priority.LOW

    @property
    def has_match(self) -> bool:
        return bool(self.matched)


def priority_from_score(score: int) -> Priority:
    if score >= 70:
        return Priority.HIGH
    if score >= 40:
        return Priority.MEDIUM
    return Priority.LOW


def analyze(text: str, rules: list[RuleLike]) -> Analysis:
    norm = normalize_text(text)
    concept = to_canonical_concept(norm)
    matched = [r for r in rules if rule_matches(norm, concept, r)]
    result = Analysis(matched=matched)
    if not matched:
        return result

    if _NEGATION.search(norm):
        result.flags.append("NEGATION")
        result.review_required = True

    if _RESOLVED.search(norm):
        result.flags.append("RESOLVED_MENTION")
        result.review_required = True

    is_planned = bool(_PLANNED.search(norm))
    if is_planned:
        result.flags.append("PLANNED")

    top_rule = max(matched, key=lambda r: r.priority)
    result.priority = priority_from_score(top_rule.priority)
    if is_planned:
        result.category = IncidentCategory.PLANNED_REPAIR
    else:
        result.category = top_rule.category

    return result
