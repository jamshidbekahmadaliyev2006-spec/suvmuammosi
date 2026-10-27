"""Matnni normalizatsiya qilish moduli.

O'zbek (lotin va kirill), rus va ingliz tillaridagi suv ta'minoti sinonimlarini qo'llab-quvvatlaydi.
Asl matn hech qachon o'zgarmaydi — faqat taqqoslash uchun nusxa normalizatsiya qilinadi.
"""
import re
import unicodedata

# O'zbek apostrof variantlari: ‘ ’ ʻ ʼ ` ´ ′ -> '
_APOSTROPHES = dict.fromkeys(map(ord, "\u2018\u2019\u02bb\u02bc`\u00b4\u2032"), "'")

_CYR_TO_LAT: dict[str, str] = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh",
    "ъ": "'", "ь": "", "э": "e", "ю": "yu", "я": "ya", "ў": "o'", "қ": "q",
    "ғ": "g'", "ҳ": "h", "ы": "i"
}

_UZ_SUFFIXES = re.compile(
    r"(?:laridan|larida|lariga|larning|larining|larimiz|laringiz|dagi|lar|ning|dan|da|ga|ni|si|i|даги|нинг|дан|да|га|ни|си|и|лар)$"
)

# Ko'p tilli (O'zbekcha Lotin/Kirill, Ruscha, Inglizcha) semantik tushunchalar xaritasi
CONCEPT_MAP: dict[str, str] = {
    # TO'SHISH / ZATOP / FLOOD
    "toshdi": "toshdi", "toshgan": "toshdi", "toshqin": "toshdi", "toshmoqda": "toshdi",
    "toshib": "toshdi", "bosdi": "toshdi", "bosgan": "toshdi", "bosmoqda": "toshdi",
    "kotarildi": "toshdi", "kotarilib": "toshdi", "ko'tarildi": "toshdi", "ko'tarilib": "toshdi",
    "затоп": "toshdi", "затопило": "toshdi", "затопила": "toshdi", "затопит": "toshdi",
    "zatop": "toshdi", "potop": "toshdi",
    "топит": "toshdi", "затапливает": "toshdi", "затопление": "toshdi", "потоп": "toshdi",
    "потопа": "toshdi", "залило": "toshdi", "заливает": "toshdi", "наводнение": "toshdi",
    "flood": "toshdi", "floods": "toshdi", "flooded": "toshdi", "flooding": "toshdi",
    "overflow": "toshdi", "overflowing": "toshdi", "inundated": "toshdi",
    "венеция": "toshdi", "venetsiya": "toshdi", "venice": "toshdi",

    # YONG'IN / POJAR / FIRE
    "yong'in": "yongin", "yongin": "yongin", "yonib": "yongin", "yondi": "yongin", "yongan": "yongin",
    "olov": "yongin", "alanga": "yongin", "ot": "yongin",
    "ёнғин": "yongin", "ёниб": "yongin", "ёнди": "yongin", "ёнган": "yongin", "олов": "yongin",
    "пожар": "yongin", "пожара": "yongin", "пожаром": "yongin", "горит": "yongin", "возгорание": "yongin",
    "возгоранием": "yongin", "огонь": "yongin", "сгорел": "yongin", "сгорела": "yongin",
    "fire": "yongin", "flame": "yongin", "burn": "yongin", "burning": "yongin",

    # QUVUR / TRUBA / PIPE
    "quvur": "quvur", "quvir": "quvur", "quvr": "quvur", "quvvur": "quvur",
    "truba": "quvur", "turba": "quvur", "vodoprovod": "quvur",
    "қувур": "quvur", "қувир": "quvur", "қувр": "quvur",
    "труба": "quvur", "трубы": "quvur", "трубу": "quvur", "трубе": "quvur", "трубой": "quvur",
    "трубах": "quvur", "трубопровод": "quvur", "водопровод": "quvur", "стояк": "quvur",
    "pipe": "quvur", "pipes": "quvur", "pipeline": "quvur", "waterpipe": "quvur",

    # YORILDI / PRORYV / BURST
    "yorildi": "yorildi", "yorilgan": "yorildi", "yorilib": "yorildi", "yoriq": "yorildi",
    "teshildi": "yorildi", "teshilgan": "yorildi", "teshik": "yorildi", "portladi": "yorildi",
    "portlagan": "yorildi", "patladi": "yorildi", "patlagan": "yorildi",
    "sindi": "yorildi", "sinib": "yorildi",
    "ёрилди": "yorildi", "ёрилган": "yorildi", "ерилди": "yorildi", "ерилган": "yorildi",
    "тешилди": "yorildi", "тешилган": "yorildi", "портлади": "yorildi", "синди": "yorildi",
    "прорыв": "yorildi", "прорвало": "yorildi", "прорвала": "yorildi", "прорвали": "yorildi",
    "лопнула": "yorildi", "лопнул": "yorildi", "лопнуло": "yorildi", "треснула": "yorildi",
    "треснул": "yorildi", "разорвало": "yorildi", "порвало": "yorildi", "пробило": "yorildi",
    "burst": "yorildi", "bursts": "yorildi", "bursting": "yorildi", "bursted": "yorildi",
    "rupture": "yorildi", "ruptured": "yorildi", "broke": "yorildi", "broken": "yorildi",

    # OQMOQDA / UTECHKA / LEAK
    "oqmoqda": "oqmoqda", "oqyapti": "oqmoqda", "oqayapti": "oqmoqda", "oqib": "oqmoqda",
    "oqishi": "oqmoqda", "sizmoqda": "oqmoqda", "sizib": "oqmoqda", "tommoqda": "oqmoqda",
    "оқмоқда": "oqmoqda", "оқяпти": "oqmoqda",
    "течет": "oqmoqda", "текут": "oqmoqda", "течь": "oqmoqda", "текла": "oqmoqda",
    "утечка": "oqmoqda", "утечки": "oqmoqda", "протекает": "oqmoqda", "протечка": "oqmoqda",
    "капает": "oqmoqda", "сочится": "oqmoqda", "хлещет": "oqmoqda",
    "leak": "oqmoqda", "leaks": "oqmoqda", "leaking": "oqmoqda", "leakage": "oqmoqda",
    "seeping": "oqmoqda", "dripping": "oqmoqda",

    # KANAL / ARIQ / CANAL / DITCH
    "kanal": "kanal", "ariq": "kanal", "daryo": "kanal", "zovur": "kanal",
    "канал": "kanal", "каналы": "kanal", "канале": "kanal", "канала": "kanal", "каналом": "kanal",
    "арык": "kanal", "арыки": "kanal", "арыке": "kanal", "река": "kanal", "реке": "kanal", "канава": "kanal",
    "canal": "kanal", "canals": "kanal", "channel": "kanal", "channels": "kanal",
    "ditch": "kanal", "ditches": "kanal", "river": "kanal",

    # CHIQINDI / AX LAT / MUSOR / TRASH
    "chiqindi": "chiqindi", "axlat": "chiqindi", "ahlat": "chiqindi", "musor": "chiqindi",
    "iflos": "chiqindi", "bulg'angan": "chiqindi", "loyqa": "chiqindi", "urna": "chiqindi",
    "чиқинди": "chiqindi", "ахлат": "chiqindi", "аҳлат": "chiqindi", "мусор": "chiqindi",
    "мусора": "chiqindi", "мусором": "chiqindi", "свалка": "chiqindi",
    "отходы": "chiqindi", "грязь": "chiqindi", "помойка": "chiqindi", "урна": "chiqindi",
    "trash": "chiqindi", "garbage": "chiqindi", "waste": "chiqindi", "debris": "chiqindi", "rubbish": "chiqindi",

    # KANALIZATSIYA / SEWAGE
    "kanalizatsiya": "kanalizatsiya", "kanalizatsya": "kanalizatsiya", "kanalizasiya": "kanalizatsiya",
    "konalizatsiya": "kanalizatsiya", "oqava": "kanalizatsiya", "kollektor": "kanalizatsiya", "lyuk": "kanalizatsiya",
    "quduq": "kanalizatsiya", "qudugi": "kanalizatsiya", "qudug'i": "kanalizatsiya",
    "qudug'iyu": "kanalizatsiya", "qudug'i-yu": "kanalizatsiya",
    "канализация": "kanalizatsiya", "канализации": "kanalizatsiya", "канализацию": "kanalizatsiya",
    "канализацией": "kanalizatsiya", "сточные": "kanalizatsiya", "стоки": "kanalizatsiya",
    "нечистоты": "kanalizatsiya", "фекалии": "kanalizatsiya", "коллектор": "kanalizatsiya",
    "люк": "kanalizatsiya", "люка": "kanalizatsiya", "люки": "kanalizatsiya", "колодец": "kanalizatsiya",
    "sewage": "kanalizatsiya", "sewer": "kanalizatsiya", "sewers": "kanalizatsiya",
    "wastewater": "kanalizatsiya", "manhole": "kanalizatsiya",

    # TIQILGAN / ZASOR / CLOGGED
    "tiqilib": "tiqilgan", "tiqilgan": "tiqilgan", "tiqilishi": "tiqilgan", "bitib": "tiqilgan",
    "тиқилиб": "tiqilgan", "тиқилган": "tiqilgan",
    "засор": "tiqilgan", "засорилась": "tiqilgan", "забилась": "tiqilgan", "забита": "tiqilgan",
    "clogged": "tiqilgan", "blocked": "tiqilgan", "blockage": "tiqilgan",

    # KOPRIK / MOST / BRIDGE
    "ko'prik": "koprik", "koprik": "koprik", "most": "koprik", "o'tkazgich": "koprik", "otkazgich": "koprik",
    "кўприк": "koprik", "мост": "koprik", "моста": "koprik", "мостом": "koprik", "мосту": "koprik", "путепровод": "koprik",
    "bridge": "koprik", "overpass": "koprik",

    # YOMG'IR / DOZHD / RAIN
    "yomg'ir": "yomgir", "yomgir": "yomgir", "jala": "yomgir", "sel": "yomgir",
    "ёмғир": "yomgir", "дождь": "yomgir", "дождя": "yomgir", "ливень": "yomgir", "ливня": "yomgir", "осадки": "yomgir",
    "rain": "yomgir", "downpour": "yomgir",

    # YERTOLA / PODVAL / BASEMENT
    "yerto'la": "yertola", "yertola": "yertola", "podval": "yertola",
    "ертўла": "yertola", "подвал": "yertola", "подвала": "yertola", "подвале": "yertola",
    "basement": "yertola", "cellar": "yertola",

    # JIJA / GRYAZ / SLUDGE
    "jija": "jija", "balchiq": "jija", "loy": "jija",
    "жижа": "jija", "слякоть": "jija", "ил": "jija",
    "sludge": "jija", "mud": "jija", "slush": "jija",

    # SUV / VODA / WATER
    "suv": "suv", "suvni": "suv", "suvning": "suv",
    "сув": "suv", "вода": "suv", "воды": "suv", "воду": "suv", "водой": "suv", "воде": "suv",
    "water": "suv",

    # SUV YO'Q / NET VODY / NO WATER
    "yo'q": "yo'q", "yoq": "yo'q", "o'chdi": "o'chdi", "ochdi": "o'chdi",
    "to'xtadi": "to'xtadi", "toxtadi": "to'xtadi",
    "йўқ": "yo'q", "йуқ": "yo'q", "ўчди": "o'chdi", "тўхтади": "to'xtadi", "сувсиз": "suvsiz",
    "outage": "suvsiz", "shutoff": "suvsiz", "cutoff": "suvsiz",

    # BOSIM / NAPOR / PRESSURE
    "bosim": "bosim", "napor": "bosim", "босим": "bosim", "напор": "bosim",
    "pressure": "bosim",

    # BUZILGAN / SLOMAN / BROKEN
    "buzilgan": "buzilgan", "buzildi": "buzilgan", "quladi": "buzilgan", "cho'kdi": "buzilgan",
    "skameka": "buzilgan", "skameyka": "buzilgan", "yolak": "buzilgan", "yo'lak": "buzilgan",
    "бузилган": "buzilgan", "бузилди": "buzilgan",
    "сломан": "buzilgan", "сломался": "buzilgan", "разрушен": "buzilgan", "разрушился": "buzilgan",
    "скамейка": "buzilgan", "лавочка": "buzilgan",
    "broken": "buzilgan", "damaged": "buzilgan", "collapsed": "buzilgan", "destroyed": "buzilgan",

    # BALIQ / RIBA / FISH
    "baliq": "baliq", "baliqlar": "baliq", "балиқ": "baliq", "балиқлар": "baliq",
    "рыба": "baliq", "рыбы": "baliq", "рыб": "baliq",
    "fish": "baliq",

    # DARAXT / DEREVO / TREE
    "daraxt": "daraxt", "daraxtlar": "daraxt", "дарахт": "daraxt", "дарахтлар": "daraxt",
    "дерево": "daraxt", "деревья": "daraxt",
    "tree": "daraxt", "trees": "daraxt",

    # PANJARA / ZABOR / FENCE
    "panjara": "panjara", "panjarasi": "panjara", "панжара": "panjara", "панжараси": "panjara",
    "забор": "panjara", "ограда": "panjara", "перила": "panjara",
    "fence": "panjara", "railing": "panjara",

    # CHOKISH / UTONUL / DROWN
    "chokish": "chokish", "cho'kish": "chokish", "chokdi": "chokish", "cho'kdi": "chokish",
    "чўкиш": "chokish", "чўкди": "chokish",
    "утонул": "chokish", "тонет": "chokish",
    "drown": "chokish", "drowning": "chokish",

    # ZAHARLANDI / OTRAVLENA / POISONED
    "zaharlandi": "zaharlandi", "zaxarlandi": "zaharlandi", "заҳарланди": "zaharlandi", "захарланди": "zaharlandi",
    "отравлена": "zaharlandi", "отравлен": "zaharlandi", "загрязнен": "zaharlandi", "загрязнена": "zaharlandi",
    "poisoned": "zaharlandi", "toxic": "zaharlandi", "contaminated": "zaharlandi",

    # HIDLANMOQDA / ZAPAX / SMELL
    "hidlanmoqda": "hidlanmoqda", "xidlanmoqda": "hidlanmoqda", "sasimoqda": "hidlanmoqda",
    "ҳидланмоқда": "hidlanmoqda", "хидланмоқда": "hidlanmoqda", "сасимоқда": "hidlanmoqda",
    "воняет": "hidlanmoqda", "запах": "hidlanmoqda", "вонь": "hidlanmoqda",
    "smell": "hidlanmoqda", "stink": "hidlanmoqda", "odor": "hidlanmoqda",

    # YOL / DOROGA / ROAD
    "yo'l": "yol", "yol": "yol", "yo'lga": "yol", "yolga": "yol", "йўл": "yol", "йўлга": "yol",
    "дорога": "yol", "дороги": "yol", "дорогу": "yol", "трасса": "yol",
    "road": "yol", "street": "yol",

    # TROTUAR / SIDEWALK
    "trotuar": "trotuar", "tratuar": "trotuar", "тратуар": "trotuar", "тротуар": "trotuar",
    "sidewalk": "trotuar", "pavement": "trotuar",

    # KIR / GRYAZ / DIRTY
    "kir": "kir", "кир": "kir", "грязная": "kir", "грязный": "kir",
    "dirty": "kir",

    # O'LGAN / MERTVIE / DEAD
    "o'lgan": "olgan", "olgan": "olgan", "ўлган": "olgan", "nobud": "olgan",
    "мертвые": "olgan", "дохлые": "olgan", "мертвая": "olgan",
    "dead": "olgan",

    # QURIB QOLDI / ZASOHLO / DRIED
    "qurib": "quridi", "quridi": "quridi", "қуриб": "quridi", "қуриган": "quridi",
    "засохло": "quridi", "высохло": "quridi",
    "dried": "quridi",

    # QAYTA MUROJAAT / JALOBI / COMPLAINT
    "murojaat": "murojaat", "мурожаат": "murojaat", "shikoyat": "murojaat",
    "жалоба": "murojaat", "обращение": "murojaat",
    "complaint": "murojaat",

    # TABIATGA ZARAR / ECOLOGY / DAMAGE
    "zarar": "zarar", "зарар": "zarar", "ekologiya": "zarar",
    "ущерб": "zarar", "вред": "zarar", "экология": "zarar",
    "damage": "zarar", "harm": "zarar",

    # CHAQMOQ / MOLNIYA / LIGHTNING / STRIKE
    "chaqmoq": "chaqmoq", "чақмоқ": "chaqmoq", "молния": "chaqmoq", "lightning": "chaqmoq",
    "urishi": "urdi", "уриши": "urdi", "urdi": "urdi", "урди": "urdi", "chaqishi": "urdi", "чақиши": "urdi", "chaqdi": "urdi", "чақди": "urdi", "ударила": "urdi", "удар": "urdi", "strike": "urdi",

    # YOG'ISH / RAIN FALLING
    "yogayotgan": "yog", "ёғаётган": "yog", "yogmoqda": "yog", "ёғмоқда": "yog", "yogayotgani": "yog", "ёғаётгани": "yog", "yogyapti": "yog", "ёғяпти": "yog", "yogib": "yog", "ёғиб": "yog",

    # SODIR / YUZ BERDI / CHIQDI / CHIKKAN / OCCURRED
    "chiqqan": "sodir", "chiqdi": "sodir", "chikgan": "sodir", "chikdi": "sodir",
    "чиққан": "sodir", "чиқди": "sodir", "чикган": "sodir", "чикди": "sodir",
    "ketipti": "sodir", "кетипти": "sodir", "ketdi": "sodir", "кетди": "sodir",
    "ketti": "sodir", "кетти": "sodir", "ketgan": "sodir", "кетган": "sodir",
    "содир": "sodir", "sodir": "sodir", "произошел": "sodir", "случился": "sodir",
    "occurred": "sodir", "happened": "sodir",
}

SYNONYMS_MAP = CONCEPT_MAP

STOP_WORDS: set[str] = {
    "va", "ham", "bilan", "uchun", "yoki", "esa", "ekan", "deb", "dep", "biri",
    "lekin", "ammo", "shuningdek", "haqida", "bu", "shu", "har", "oz", "o'z",
    "juda", "bo'yicha", "boyicha", "tomonidan",
    "v", "na", "i", "the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "is", "are",
}

CANONICAL_TARGETS: list[str] = [
    "quvur", "yorildi", "teshildi", "toshdi", "bosdi", "oqmoqda",
    "kanalizatsiya", "lyuk", "avariya", "ta'mirlash", "to'xtadi",
    "kanal", "chiqindi", "yomgir", "koprik", "panjara"
]


def _levenshtein(s1: str, s2: str) -> int:
    if s1 == s2:
        return 0
    if len(s1) < len(s2):
        s1, s2 = s2, s1
    if not s2:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1] * (len(s2) + 1)
        for j, c2 in enumerate(s2):
            curr[j + 1] = min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (0 if c1 == c2 else 1))
        prev = curr
    return prev[-1]


def cyrillic_to_latin(text: str) -> str:
    """Kirill yozuvidagi matnni lotin alifbosiga o'giradi."""
    res = []
    for ch in text.lower():
        res.append(_CYR_TO_LAT.get(ch, ch))
    return "".join(res)


def strip_uz_suffixes(word: str) -> str:
    """O'zbekcha so'z yasovchi va kelishik qo'shimchalarini tozalaydi."""
    curr = word
    while True:
        prev = curr
        curr = _UZ_SUFFIXES.sub("", curr)
        if curr == prev or len(curr) < 3:
            break
    return curr


def normalize_text(text: str) -> str:
    """Matnni asosiy taqqoslash uchun normalizatsiya qiladi: apostroflar, NFKC va case folding."""
    if not text:
        return ""
    text = text.translate(_APOSTROPHES)
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_APOSTROPHES).casefold()

    words = text.split()
    normalized_words: list[str] = []
    for w in words:
        clean = w.strip(".,!?:;\"()[]{}<>~`'’«»“”—–-")
        if not clean:
            continue
        if clean in SYNONYMS_MAP:
            normalized_words.append(SYNONYMS_MAP[clean])
            continue
        if len(clean) >= 4:
            stem = _UZ_SUFFIXES.sub("", clean)
            if stem in SYNONYMS_MAP:
                normalized_words.append(SYNONYMS_MAP[stem])
                continue
        matched_target: str | None = None
        if clean.isascii() and clean.isalpha():
            for target in CANONICAL_TARGETS:
                if len(clean) >= 4 and abs(len(clean) - len(target)) <= 2:
                    max_diff = 2 if len(target) >= 6 else 1
                    if _levenshtein(clean, target) <= max_diff:
                        matched_target = target
                        break
        normalized_words.append(matched_target or clean)

    return " ".join(normalized_words)


def to_canonical_concept(text: str) -> str:
    """Matnni ko'p tilli (o'zbek, rus, ingliz) semantik tushunchalarga ajratadi."""
    if not text:
        return ""
    text = text.translate(_APOSTROPHES)
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_APOSTROPHES).casefold()

    words = text.split()
    tokens: list[str] = []
    for w in words:
        clean = w.strip(".,!?:;\"()[]{}<>~`'’«»“”—–-")
        if not clean:
            continue

        if clean in CONCEPT_MAP:
            tokens.append(CONCEPT_MAP[clean])
            continue

        if any("\u0400" <= c <= "\u04ff" for c in clean):
            lat = cyrillic_to_latin(clean)
            if lat in CONCEPT_MAP:
                tokens.append(CONCEPT_MAP[lat])
                continue
            lat_stem = strip_uz_suffixes(lat)
            if lat_stem in CONCEPT_MAP:
                tokens.append(CONCEPT_MAP[lat_stem])
                continue
            tokens.append(lat_stem if len(lat_stem) >= 3 else lat)
            continue

        stem = strip_uz_suffixes(clean)
        if stem in CONCEPT_MAP:
            tokens.append(CONCEPT_MAP[stem])
            continue

        tokens.append(stem if len(stem) >= 3 else clean)

    return " ".join(tokens)


def extract_key_tokens(norm_text: str) -> list[str]:
    """Tushunchalar ichidan asosiy qidiruv kalit so'zlarini ajratib oladi."""
    raw = [t for t in re.split(r"[^\w']+", norm_text) if t]
    filtered = [t for t in raw if t not in STOP_WORDS]
    return filtered if filtered else raw
