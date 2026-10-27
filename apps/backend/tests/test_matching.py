from types import SimpleNamespace

import pytest

from app.models.enums import IncidentCategory, MatchType
from app.services.matching import analyze
from app.services.text import normalize_text


def rule(keyword, match_type=MatchType.PHRASE, category=IncidentCategory.PIPE_BURST, priority=80,
         id_=1):
    return SimpleNamespace(id=id_, keyword_normalized=normalize_text(keyword),
                           match_type=match_type, category=category, priority=priority)


def test_simple_match():
    assert analyze("Quvur yorildi!", [rule("quvur yorildi")]).has_match


def test_case_insensitive():
    assert analyze("QUVUR YORILDI", [rule("quvur yorildi")]).has_match


@pytest.mark.parametrize("apos", ["'", "’", "‘", "ʻ", "ʼ"])
def test_apostrophe_variants(apos):
    text = f"Suv o{apos}chdi mahallada"
    assert analyze(text, [rule("suv o'chdi")]).has_match
    assert analyze("suv o'chdi", [rule(f"suv o{apos}chdi")]).has_match


def test_extra_whitespace_and_newlines():
    assert analyze("quvur   \n yorildi", [rule("quvur yorildi")]).has_match


def test_original_text_not_modified_by_normalization():
    original = "Suv O‘CHDI"
    normalize_text(original)
    assert original == "Suv O‘CHDI"


def test_contains_vs_whole_word_vs_phrase():
    assert analyze("suvsiz qoldik", [rule("suv", MatchType.CONTAINS)]).has_match
    assert not analyze("suvsiz qoldik", [rule("suv", MatchType.WHOLE_WORD)]).has_match
    assert analyze("suv yo'q.", [rule("suv", MatchType.WHOLE_WORD)]).has_match
    assert analyze("suv, yo'q", [rule("suv yo'q", MatchType.PHRASE)]).has_match
    assert not analyze("suv yo'q", [rule("suv bor", MatchType.PHRASE)]).has_match


def test_negation_needs_review_not_incident():
    a = analyze("Suv ta'minoti muammosi yo'q, suv ta'minoti muammosi hal",
                [rule("suv ta'minoti muammosi")])
    assert a.has_match and a.review_required and "NEGATION" in a.flags


def test_resolved_phrase_needs_review():
    a = analyze("Quvur yorildi, hozir tuzatildi", [rule("quvur yorildi")])
    assert a.review_required and "RESOLVED_MENTION" in a.flags


def test_planned_work_recognized():
    a = analyze("Ertaga quvur yorildi ta'mirlanadi", [rule("quvur yorildi")])
    assert a.category == IncidentCategory.PLANNED_REPAIR and not a.review_required


def test_real_failure_is_not_planned():
    a = analyze("Quvur yorildi, mahallada suv oqmoqda", [rule("quvur yorildi")])
    assert a.category == IncidentCategory.PIPE_BURST and not a.review_required


def test_no_match():
    assert not analyze("Bugun ob-havo yaxshi", [rule("quvur yorildi")]).has_match
