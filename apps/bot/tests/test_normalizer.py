from services.normalizer import normalize_text


def test_normalize_empty_text():
    assert normalize_text("") == ""
    assert normalize_text("   ") == ""


def test_normalize_apostrophes():
    # Barcha apostrof variantlari bitta ' ga aylanishi kerak
    variants = [
        "suv yo'q",
        "suv yo‘q",
        "suv yo’q",
        "suv yoʻq",
        "suv yoʼq",
        "suv yo`q",
        "suv yo´q",
        "suv yo′q",
    ]
    for variant in variants:
        assert normalize_text(variant) == "suv yo'q"


def test_normalize_case_folding():
    assert normalize_text("QUVUR YORILDI") == "quvur yorildi"
    assert normalize_text("SuV Yo'Q") == "suv yo'q"
    assert normalize_text("ТА'МИРЛАШ") == "та'мирлаш"


def test_normalize_whitespace_and_newlines():
    text = "   quvur \n\n   yorildi \t  ko'chada   "
    assert normalize_text(text) == "quvur yorildi ko'chada"
