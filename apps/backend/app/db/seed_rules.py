"""Boshlang'ich kalit so'zlar. Ular bazaga yoziladi va sayt orqali boshqariladi.

O'zbek, Rus va Ingliz tillaridagi asosiy monitoring qoidalari.
"""
from app.models.enums import IncidentCategory as C

SEED_RULES: list[tuple[str, str, C, int]] = [
    # ==================== O'ZBEKCHA ====================
    # Quvur / Truba muammolari
    ("Quvur yorildi", "quvur yorildi", C.PIPE_BURST, 80),
    ("Quvur teshildi", "quvur teshildi", C.PIPE_BURST, 80),
    ("Quvur avariyasi", "quvur avariyasi", C.PIPE_BURST, 80),
    ("Truba yorildi", "truba yorildi", C.PIPE_BURST, 80),
    ("Quvur", "quvur", C.PIPE_BURST, 60),

    # Suv toshishi va toshqin
    ("Suv toshdi", "suv toshdi", C.FLOODING, 85),
    ("Suv bosdi", "suv bosdi", C.FLOODING, 85),
    ("Ko'chani suv bosdi", "ko'chani suv bosdi", C.FLOODING, 80),
    ("Toshqin", "toshqin", C.FLOODING, 75),

    # Suv ta'minoti to'xtashi va yo'qligi
    ("Suv yo'q", "suv yo'q", C.SUPPLY_OUTAGE, 60),
    ("Suv o'chdi", "suv o'chdi", C.SUPPLY_OUTAGE, 60),
    ("Suv kelmayapti", "suv kelmayapti", C.SUPPLY_OUTAGE, 65),
    ("Suvsiz qoldik", "suvsiz", C.SUPPLY_OUTAGE, 60),
    ("Suv ta'minoti to'xtadi", "suv ta'minoti to'xtadi", C.SUPPLY_OUTAGE, 70),
    ("Suv ta'minoti muammosi", "suv ta'minoti muammosi", C.SUPPLY_OUTAGE, 50),

    # Bosim va napor
    ("Suv bosimi pasaydi", "suv bosimi pasaydi", C.LOW_PRESSURE, 50),
    ("Bosim yo'q", "bosim yo'q", C.LOW_PRESSURE, 50),
    ("Napor yo'q", "napor yo'q", C.LOW_PRESSURE, 55),
    ("Napor past", "napor past", C.LOW_PRESSURE, 50),

    # Oqish va sizish
    ("Suv oqmoqda", "suv oqmoqda", C.LEAK, 40),
    ("Suv oqyapti", "suv oqyapti", C.LEAK, 45),
    ("Suv sizib chiqmoqda", "suv sizib chiqmoqda", C.LEAK, 40),

    # Kanalizatsiya va oqova
    ("Kanalizatsiya avariyasi", "kanalizatsiya avariyasi", C.SEWAGE, 85),
    ("Kanalizatsiya toshdi", "kanalizatsiya toshdi", C.SEWAGE, 85),
    ("Kanalizatsiya", "kanalizatsiya", C.SEWAGE, 75),
    ("Ochiq lyuk", "lyuk ochiq", C.SEWAGE, 70),

    # Ta'mirlash
    ("Ta'mirlash ishlari", "ta'mirlash ishlari", C.PLANNED_REPAIR, 20),
    ("Vaqtincha suv to'xtatilishi", "vaqtincha suv to'xtatilishi", C.PLANNED_REPAIR, 30),

    # ==================== РУССКИЙ ЯЗЫК ====================
    ("Прорыв трубы", "прорыв трубы", C.PIPE_BURST, 85),
    ("Авария водопровода", "авария водопровода", C.PIPE_BURST, 80),
    ("Утечка воды", "утечка воды", C.LEAK, 50),
    ("Течет вода", "течет вода", C.LEAK, 45),
    ("Нет воды", "нет воды", C.SUPPLY_OUTAGE, 65),
    ("Отключение воды", "отключение воды", C.SUPPLY_OUTAGE, 65),
    ("Слабый напор воды", "слабый напор", C.LOW_PRESSURE, 55),
    ("Низкое давление воды", "низкое давление", C.LOW_PRESSURE, 50),
    ("Затопило", "затопило", C.FLOODING, 85),
    ("Потоп", "потоп", C.FLOODING, 80),
    ("Авария канализации", "авария канализации", C.SEWAGE, 75),
    ("Открытый люк", "открытый люк", C.SEWAGE, 70),
    ("Плановые ремонтные работы", "плановый ремонт", C.PLANNED_REPAIR, 25),

    # ==================== ENGLISH ====================
    ("Pipe burst", "pipe burst", C.PIPE_BURST, 85),
    ("Water leak", "water leak", C.LEAK, 50),
    ("No water", "no water", C.SUPPLY_OUTAGE, 65),
    ("Water outage", "water outage", C.SUPPLY_OUTAGE, 65),
    ("Low water pressure", "low pressure", C.LOW_PRESSURE, 55),
    ("Flooding", "flooding", C.FLOODING, 85),
    ("Sewage problem", "sewage", C.SEWAGE, 75),
    ("Open manhole", "manhole", C.SEWAGE, 70),
    ("Planned maintenance", "maintenance", C.PLANNED_REPAIR, 25),
]
