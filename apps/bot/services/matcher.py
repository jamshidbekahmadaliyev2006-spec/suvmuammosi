"""Telegram xabarlarini dinamik qoidalar asosida tekshirish moduli."""
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from .normalizer import STOP_WORDS, extract_key_tokens, normalize_text, to_canonical_concept

_BOUNDARY_BEFORE = r"(?<![\w'])"
_BOUNDARY_AFTER = r"(?![\w'])"
_CONNECTOR = r"(?:[^\w']+(?:[\w']{1,15}[^\w']+)?|[^\w']+)"


@lru_cache(maxsize=2048)
def _compile_pattern(keyword: str, match_type: str) -> re.Pattern[str]:
    """ReDoS xavfisiz xavfsiz regex pattern yaratish."""
    norm_kw = normalize_text(keyword)
    mt = match_type.upper()
    if mt == "CONTAINS":
        return re.compile(re.escape(norm_kw))
    if mt == "WHOLE_WORD":
        return re.compile(_BOUNDARY_BEFORE + re.escape(norm_kw) + _BOUNDARY_AFTER)
    tokens = [t for t in re.split(r"[^\w']+", norm_kw) if t]
    if len(tokens) == 2:
        p1 = re.escape(tokens[0]) + _CONNECTOR + re.escape(tokens[1])
        p2 = re.escape(tokens[1]) + _CONNECTOR + re.escape(tokens[0])
        body = f"(?:{p1}|{p2})"
    else:
        body = _CONNECTOR.join(re.escape(t) for t in tokens)
    return re.compile(_BOUNDARY_BEFORE + body + _BOUNDARY_AFTER)


@lru_cache(maxsize=4096)
def _compile_rule_patterns(keyword: str, match_type: str) -> list[re.Pattern[str]]:
    """To'g'ridan-to'g'ri va ko'p tilli (lotin, kirill, rus, ingliz) semantik qoliplar."""
    direct_pat = _compile_pattern(keyword, match_type)
    patterns = [direct_pat]

    # Semantik tushunchalar qolipi
    mt = match_type.upper()
    if mt != "CONTAINS":
        concept_kw = to_canonical_concept(keyword)
        key_tokens = extract_key_tokens(concept_kw)
        raw_words = [t for t in re.split(r"[^\w']+", keyword) if t and t not in STOP_WORDS]
        if key_tokens:
            if len(key_tokens) == 1:
                if len(raw_words) <= 1:
                    patterns.append(re.compile(_BOUNDARY_BEFORE + re.escape(key_tokens[0]) + _BOUNDARY_AFTER))
            elif len(key_tokens) == 2:
                cp1 = re.escape(key_tokens[0]) + _CONNECTOR + re.escape(key_tokens[1])
                cp2 = re.escape(key_tokens[1]) + _CONNECTOR + re.escape(key_tokens[0])
                patterns.append(re.compile(_BOUNDARY_BEFORE + f"(?:{cp1}|{cp2})" + _BOUNDARY_AFTER))
            else:
                body = _CONNECTOR.join(re.escape(t) for t in key_tokens)
                patterns.append(re.compile(_BOUNDARY_BEFORE + body + _BOUNDARY_AFTER))

    return patterns


# Kontekst qoliplari (O'zbekcha, Ruscha, Inglizcha)
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
class MatchResult:
    has_match: bool = False
    matched_rules: list[dict[str, Any]] = field(default_factory=list)
    matched_rule_ids: list[int] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    is_planned: bool = False
    is_negation: bool = False
    is_resolved: bool = False
    top_priority: int = 0
    top_category: str | None = None


def match_message(text: str, active_rules: list[dict[str, Any]]) -> MatchResult:
    """Xabar matnini berilgan faol qoidalar bilan solishtiradi."""
    if not text or not active_rules:
        return MatchResult()

    norm_text = normalize_text(text)
    concept_text: str | None = None
    matched: list[dict[str, Any]] = []

    for rule in active_rules:
        kw = rule.get("keyword", "")
        mt = rule.get("match_type", "PHRASE")
        patterns = _compile_rule_patterns(kw, mt)

        is_match = patterns[0].search(norm_text) is not None
        if not is_match and len(patterns) > 1:
            if concept_text is None:
                concept_text = to_canonical_concept(norm_text)
            for pat in patterns[1:]:
                if pat.search(concept_text) is not None:
                    is_match = True
                    break

        if is_match:
            matched.append(rule)

    if not matched:
        return MatchResult(has_match=False)

    flags: list[str] = []
    is_negation = bool(_NEGATION.search(norm_text))
    if is_negation:
        flags.append("NEGATION")

    is_resolved = bool(_RESOLVED.search(norm_text))
    if is_resolved:
        flags.append("RESOLVED_MENTION")

    is_planned = bool(_PLANNED.search(norm_text))
    if is_planned:
        flags.append("PLANNED")

    top_rule = max(matched, key=lambda r: r.get("priority", 0))
    category = "PLANNED_REPAIR" if is_planned else top_rule.get("category")

    return MatchResult(
        has_match=True,
        matched_rules=matched,
        matched_rule_ids=[r["id"] for r in matched if "id" in r],
        flags=flags,
        is_planned=is_planned,
        is_negation=is_negation,
        is_resolved=is_resolved,
        top_priority=top_rule.get("priority", 0),
        top_category=category,
    )
