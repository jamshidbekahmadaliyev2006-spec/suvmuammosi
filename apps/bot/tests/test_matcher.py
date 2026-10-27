from services.matcher import match_message


def test_matcher_contains_match(sample_rules):
    # 'oqmoqda' CONTAINS rejimida
    res = match_message("katta tezlikda suv oqmoqda ko'chada", sample_rules)
    assert res.has_match is True
    assert 4 in res.matched_rule_ids
    assert res.top_category == "LEAK"


def test_matcher_whole_word_match(sample_rules):
    # 'kanalizatsiya' WHOLE_WORD
    res = match_message("bu yerda kanalizatsiya teshildi", sample_rules)
    assert res.has_match is True
    assert 3 in res.matched_rule_ids

    # So'zning bir qismi bo'lsa mos kelmasligi kerak: 'kanalizatsiyasiz'
    res_partial = match_message("kanalizatsiyasiz hudud", sample_rules)
    assert 3 not in res_partial.matched_rule_ids


def test_matcher_phrase_match(sample_rules):
    # 'quvur yorildi' PHRASE
    res = match_message("Bugun ertalab quvur   yorildi markazda", sample_rules)
    assert res.has_match is True
    assert 1 in res.matched_rule_ids
    assert res.top_priority == 80


def test_matcher_negation_flag(sample_rules):
    # Inkor mazmundagi xabar
    text = "Hozircha hech qanday suv yo'q muammosi kuzatilmadi"
    res = match_message(text, sample_rules)
    assert res.has_match is True
    assert res.is_negation is True
    assert "NEGATION" in res.flags


def test_matcher_resolved_flag(sample_rules):
    # Hal qilingan / tiklangan xabar
    text = "Quvur yorildi deb xabar qilingan edi, ammo nosozlik to'liq bartaraf etildi"
    res = match_message(text, sample_rules)
    assert res.has_match is True
    assert res.is_resolved is True
    assert "RESOLVED_MENTION" in res.flags


def test_matcher_planned_repair(sample_rules):
    # Rejali ta'mirlash xabari
    text = "Ertaga quvur yorildi deb taxmin qilingan joyda ta'mirlanadi"
    res = match_message(text, sample_rules)
    assert res.has_match is True
    assert res.is_planned is True
    assert "PLANNED" in res.flags
    assert res.top_category == "PLANNED_REPAIR"


def test_matcher_no_match(sample_rules):
    res = match_message("Bugun ob-havo quyoshli bo'ladi", sample_rules)
    assert res.has_match is False
    assert len(res.matched_rule_ids) == 0
