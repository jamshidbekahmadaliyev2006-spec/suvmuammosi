"""Matndan shahar, tuman va aniq manzil (ko'cha, mavze, uy) ma'lumotlarini aniqlash moduli.
Shahar hokimiyati tizimi uchun maxsus ishlab chiqilgan.
"""
import re
from typing import Tuple

from app.services.geocoding import reverse_geocode

# Toshkent shahri va viloyat tumanlari
TASHKENT_DISTRICTS = {
    # Lotin yozuvi
    "yunusobod": "Yunusobod tumani",
    "yunusabot": "Yunusobod tumani",
    "yunusabad": "Yunusobod tumani",
    "yunusobot": "Yunusobod tumani",
    "chilonzor": "Chilonzor tumani",
    "chilonzar": "Chilonzor tumani",
    "chilanzar": "Chilonzor tumani",
    "mirzo ulug'bek": "Mirzo Ulug'bek tumani",
    "mirzo ulugbek": "Mirzo Ulug'bek tumani",
    "mirzo-ulug'bek": "Mirzo Ulug'bek tumani",
    "yakkasaroy": "Yakkasaroy tumani",
    "yakkasaray": "Yakkasaroy tumani",
    "shayxontohur": "Shayxontohur tumani",
    "shayxontoxur": "Shayxontohur tumani",
    "shayhontohur": "Shayxontohur tumani",
    "olmazor": "Olmazor tumani",
    "almazar": "Olmazor tumani",
    "uchtepa": "Uchtepa tumani",
    "sergeli": "Sergeli tumani",
    "sergili": "Sergeli tumani",
    "sirg'ali": "Sergeli tumani",
    "mirobod": "Mirobod tumani",
    "mirabad": "Mirobod tumani",
    "mirobot": "Mirobod tumani",
    "yashnobod": "Yashnobod tumani",
    "yashnobot": "Yashnobod tumani",
    "yashnabad": "Yashnobod tumani",
    "bektemir": "Bektemir tumani",
    "yangihayot": "Yangihayot tumani",

    # Ruscha va Kirill yozuvidagi Toshkent tumanlari
    "юнусобод": "Yunusobod tumani",
    "юнусабад": "Yunusobod tumani",
    "чилонзор": "Chilonzor tumani",
    "чиланзар": "Chilonzor tumani",
    "мирзо улуғбек": "Mirzo Ulug'bek tumani",
    "мирзо улугбек": "Mirzo Ulug'bek tumani",
    "мирзо-улугбек": "Mirzo Ulug'bek tumani",
    "яккасарой": "Yakkasaroy tumani",
    "яккасарай": "Yakkasaroy tumani",
    "шайхонтоҳур": "Shayxontohur tumani",
    "шайхантахур": "Shayxontohur tumani",
    "олмазор": "Olmazor tumani",
    "алмазар": "Olmazor tumani",
    "учтепа": "Uchtepa tumani",
    "сергели": "Sergeli tumani",
    "сиргали": "Sergeli tumani",
    "миробод": "Mirobod tumani",
    "мирабад": "Mirobod tumani",
    "яшнобод": "Yashnobod tumani",
    "яшнабад": "Yashnobod tumani",
    "бектемир": "Bektemir tumani",
    "янгиҳаёт": "Yangihayot tumani",
    "янгихает": "Yangihayot tumani",
}

OTHER_CITIES = {
    "samarqand": "Samarqand shahri",
    "buxoro": "Buxoro shahri",
    "andijon": "Andijon shahri",
    "farg'ona": "Farg'ona shahri",
    "fargona": "Farg'ona shahri",
    "namangan": "Namangan shahri",
    "qarshi": "Qarshi shahri",
    "nukus": "Nukus shahri",
    "urganch": "Urganch shahri",
    "navoiy": "Navoiy shahri",
    "jizzax": "Jizzax shahri",
    "guliston": "Guliston shahri",
    "termiz": "Termiz shahri",
    "chirchiq": "Chirchiq shahri",
    "angren": "Angren shahri",
    "olmaliq": "Olmaliq shahri",
    "bekobod": "Bekobod shahri",
    "yangiyo'l": "Yangiyo'l shahri",
    "yangiyol": "Yangiyo'l shahri",
    "qo'qon": "Qo'qon shahri",
    "qoqon": "Qo'qon shahri",
    "marg'ilon": "Marg'ilon shahri",
    # Kirill / Ruscha
    "самарқанд": "Samarqand shahri",
    "самарканд": "Samarqand shahri",
    "бухоро": "Buxoro shahri",
    "бухара": "Buxoro shahri",
    "андижон": "Andijon shahri",
    "андижан": "Andijon shahri",
    "фарғона": "Farg'ona shahri",
    "фергана": "Farg'ona shahri",
    "наманган": "Namangan shahri",
    "қарши": "Qarshi shahri",
    "карши": "Qarshi shahri",
    "нукус": "Nukus shahri",
    "урганч": "Urganch shahri",
    "ургенч": "Urganch shahri",
    "навоий": "Navoiy shahri",
    "навои": "Navoiy shahri",
    "жиззах": "Jizzax shahri",
    "джизак": "Jizzax shahri",
    "гулистон": "Guliston shahri",
    "гулистан": "Guliston shahri",
    "термиз": "Termiz shahri",
    "термез": "Termiz shahri",
    "чирчиқ": "Chirchiq shahri",
    "чирчик": "Chirchiq shahri",
    "ангрен": "Angren shahri",
    "олмалиқ": "Olmaliq shahri",
    "алмалык": "Olmaliq shahri",
    "бекобод": "Bekobod shahri",
    "бекабад": "Bekobod shahri",
}

# Ko'cha, mavze va mashhur joy nomlaridan Toshkent tumanini aniqlash xaritasi
TASHKENT_STREET_DISTRICT_MAP: dict[str, str] = {
    # Olmazor tumani
    "sebzor": "Olmazor tumani",
    "себзор": "Olmazor tumani",
    "beruniy": "Olmazor tumani",
    "беруний": "Olmazor tumani",
    "qorasaroy": "Olmazor tumani",
    "қорасарой": "Olmazor tumani",
    "корасарой": "Olmazor tumani",
    "qoraqamish": "Olmazor tumani",
    "қорақamish": "Olmazor tumani",
    "коракамыш": "Olmazor tumani",
    "sag'bon": "Olmazor tumani",
    "сағбон": "Olmazor tumani",
    "сагбон": "Olmazor tumani",
    "chig'atoy": "Olmazor tumani",
    "чиғатой": "Olmazor tumani",
    "zarqaynar": "Olmazor tumani",
    "зарқайнар": "Olmazor tumani",
    "langar": "Olmazor tumani",
    "лангар": "Olmazor tumani",
    "tinchlik": "Olmazor tumani",
    "тинчлик": "Olmazor tumani",
    "talabalar": "Olmazor tumani",
    "талабалар": "Olmazor tumani",
    "shifokorlar": "Olmazor tumani",

    # Chilonzor tumani
    "katartal": "Chilonzor tumani",
    "катартал": "Chilonzor tumani",
    "qatortol": "Chilonzor tumani",
    "қатортол": "Chilonzor tumani",
    "lutfiy": "Chilonzor tumani",
    "лутфий": "Chilonzor tumani",
    "muqimiy": "Chilonzor tumani",
    "муқимий": "Chilonzor tumani",
    "мукими": "Chilonzor tumani",
    "cho'ponota": "Chilonzor tumani",
    "чупонота": "Chilonzor tumani",
    "chaponota": "Chilonzor tumani",
    "bunyodkor": "Chilonzor tumani",
    "бунёдкор": "Chilonzor tumani",
    "al-xorazmiy": "Chilonzor tumani",
    "ал-хоразмий": "Chilonzor tumani",
    "xorazmiy": "Chilonzor tumani",
    "хоразмий": "Chilonzor tumani",
    "do'mbrobod": "Chilonzor tumani",
    "домбрабад": "Chilonzor tumani",
    "gavhar": "Chilonzor tumani",
    "гавхар": "Chilonzor tumani",
    "baynalminal": "Chilonzor tumani",
    "байналминал": "Chilonzor tumani",

    # Yunusobod tumani
    "ahmad donish": "Yunusobod tumani",
    "ахмад дониш": "Yunusobod tumani",
    "amir temur": "Yunusobod tumani",
    "амир темур": "Yunusobod tumani",
    "bog'ishamol": "Yunusobod tumani",
    "боғишамол": "Yunusobod tumani",
    "богишамол": "Yunusobod tumani",
    "shaxriston": "Yunusobod tumani",
    "шахристон": "Yunusobod tumani",
    "chinobod": "Yunusobod tumani",
    "чинобод": "Yunusobod tumani",
    "hasanboy": "Yunusobod tumani",
    "хасанбой": "Yunusobod tumani",
    "tiklanish": "Yunusobod tumani",
    "тикланиш": "Yunusobod tumani",
    "otchopar": "Yunusobod tumani",
    "отчопар": "Yunusobod tumani",
    "kulolqo'rg'on": "Yunusobod tumani",
    "minor": "Yunusobod tumani",
    "минор": "Yunusobod tumani",

    # Mirzo Ulug'bek tumani
    "buyuk ipak yo'li": "Mirzo Ulug'bek tumani",
    "буюк ипак йўли": "Mirzo Ulug'bek tumani",
    "буюк ипак йули": "Mirzo Ulug'bek tumani",
    "maksim gorkiy": "Mirzo Ulug'bek tumani",
    "максим горький": "Mirzo Ulug'bek tumani",
    "qorasuv": "Mirzo Ulug'bek tumani",
    "қорасув": "Mirzo Ulug'bek tumani",
    "карасу": "Mirzo Ulug'bek tumani",
    "feroza": "Mirzo Ulug'bek tumani",
    "фероза": "Mirzo Ulug'bek tumani",
    "dormon": "Mirzo Ulug'bek tumani",
    "дўрмон": "Mirzo Ulug'bek tumani",
    "дурмон": "Mirzo Ulug'bek tumani",
    "ziyolilar": "Mirzo Ulug'bek tumani",
    "зиёлилар": "Mirzo Ulug'bek tumani",
    "traktorsozlar": "Mirzo Ulug'bek tumani",
    "тракторсозлар": "Mirzo Ulug'bek tumani",
    "olamzor": "Mirzo Ulug'bek tumani",
    "оламзор": "Mirzo Ulug'bek tumani",

    # Shayxontohur tumani
    "navoiy": "Shayxontohur tumani",
    "навоий": "Shayxontohur tumani",
    "навои": "Shayxontohur tumani",
    "samarqand darvoza": "Shayxontohur tumani",
    "самарқанд дарвоза": "Shayxontohur tumani",
    "xadra": "Shayxontohur tumani",
    "хадра": "Shayxontohur tumani",
    "chorsu": "Shayxontohur tumani",
    "чорсу": "Shayxontohur tumani",
    "labzak": "Shayxontohur tumani",
    "лабзак": "Shayxontohur tumani",
    "ko'kcha": "Shayxontohur tumani",
    "кўкча": "Shayxontohur tumani",
    "кукча": "Shayxontohur tumani",
    "beltepa": "Shayxontohur tumani",
    "белтепа": "Shayxontohur tumani",
    "jarariq": "Shayxontohur tumani",
    "жарариқ": "Shayxontohur tumani",

    # Uchtepa tumani
    "farhod": "Uchtepa tumani",
    "фарҳод": "Uchtepa tumani",
    "фарход": "Uchtepa tumani",
    "foziltepa": "Uchtepa tumani",
    "фозилтепа": "Uchtepa tumani",
    "o'rikzor": "Uchtepa tumani",
    "ўрикзор": "Uchtepa tumani",
    "урикзор": "Uchtepa tumani",
    "tutzor": "Uchtepa tumani",
    "тутзор": "Uchtepa tumani",
    "birlik": "Uchtepa tumani",
    "бирлик": "Uchtepa tumani",
    "ko'rkam": "Uchtepa tumani",
    "куркам": "Uchtepa tumani",

    # Yakkasaroy tumani
    "shota rustaveli": "Yakkasaroy tumani",
    "шота руставели": "Yakkasaroy tumani",
    "rustaveli": "Yakkasaroy tumani",
    "руставели": "Yakkasaroy tumani",
    "bobur": "Yakkasaroy tumani",
    "бобур": "Yakkasaroy tumani",
    "kosmonavtlar": "Yakkasaroy tumani",
    "космонавтлар": "Yakkasaroy tumani",
    "boshliq": "Yakkasaroy tumani",
    "бошлиқ": "Yakkasaroy tumani",
    "бошлик": "Yakkasaroy tumani",
    "qushbegi": "Yakkasaroy tumani",
    "қушбеги": "Yakkasaroy tumani",

    # Mirobod tumani
    "nukus": "Mirobod tumani",
    "нукус": "Mirobod tumani",
    "oybek": "Mirobod tumani",
    "ойбек": "Mirobod tumani",
    "shahrisabz": "Mirobod tumani",
    "шаҳрисабз": "Mirobod tumani",
    "шахрисабз": "Mirobod tumani",
    "sariko'l": "Mirobod tumani",
    "сарикўл": "Mirobod tumani",
    "gospital": "Mirobod tumani",
    "госпиталь": "Mirobod tumani",
    "afrosiyob": "Mirobod tumani",
    "афросиёб": "Mirobod tumani",
    "qo'yliq": "Mirobod tumani",
    "қўйлиқ": "Mirobod tumani",
    "куйлюк": "Mirobod tumani",

    # Yashnobod tumani
    "tuzel": "Yashnobod tumani",
    "тузель": "Yashnobod tumani",
    "aviasozlar": "Yashnobod tumani",
    "авиасозлар": "Yashnobod tumani",
    "kadisheva": "Yashnobod tumani",
    "кадышева": "Yashnobod tumani",
    "farg'ona yo'li": "Yashnobod tumani",
    "фарғона йўли": "Yashnobod tumani",
    "ферганское шоссе": "Yashnobod tumani",
    "parkent": "Yashnobod tumani",
    "паркент": "Yashnobod tumani",
    "elbek": "Yashnobod tumani",
    "эльбек": "Yashnobod tumani",
    "ohangaron": "Yashnobod tumani",
    "ахангаран": "Yashnobod tumani",
    "mashinasozlar": "Yashnobod tumani",
    "машинасозлар": "Yashnobod tumani",

    # Sergeli tumani
    "yangi sergeli": "Sergeli tumani",
    "янги сергели": "Sergeli tumani",
    "qipchoq": "Sergeli tumani",
    "қипчоқ": "Sergeli tumani",
    "кипчак": "Sergeli tumani",
    "so'g'diyona": "Sergeli tumani",
    "соғдиёна": "Sergeli tumani",
    "chortoq": "Sergeli tumani",
    "чортоқ": "Sergeli tumani",

    # Yangihayot tumani
    "yo'ldosh": "Yangihayot tumani",
    "йўлдош": "Yangihayot tumani",
    "юлдаш": "Yangihayot tumani",
    "binokor": "Yangihayot tumani",
    "бинокор": "Yangihayot tumani",
    "xushnud": "Yangihayot tumani",
    "хушнуд": "Yangihayot tumani",

    # Bektemir tumani
    "vodnik": "Bektemir tumani",
    "водник": "Bektemir tumani",
    "majlis": "Bektemir tumani",
}


# Manzil qismlari uchun regex qoliplari
_MAVZE_PATTERNS = [
    re.compile(r"(\d+)[ -]?(?:chi)?\s*(?:mavze|kvartal|massiv|mikrorayon|квартал|массив|микрорайон|daha|kv|mavz)\b", re.IGNORECASE),
    re.compile(r"\b(?:mavze|kvartal|massiv|mikrorayon|квартал|массив|микрорайон|daha|kv|mavz)[ -]?(\d+)", re.IGNORECASE),
    re.compile(r"([A-Za-zА-Яа-яʻʼ'\d\s-]+)\s*(?:mavzesi|kvartali|massivi|квартали|массиви)", re.IGNORECASE),
]

_STREET_PATTERNS = [
    re.compile(r"(?:ул\.|улица|проспект|пр-т|проезд)\s+([A-ZА-Яa-zа-яʻʼ'\d\s-]+?)(?=,\s*|\s+(?:дом|д\.|квартира|кв\.|массив|квартал|этаж)|\s*$)", re.IGNORECASE),
    re.compile(r"([A-ZА-Яa-zа-яʻʼ'\d\s-]+?)\s*(?:ko'chasi|ko‘chasi|kuchasi|kochasi|ko'cha|ko‘cha|кўчаси|кўча|проспекти|проспект|shoh\s+ko'chasi)", re.IGNORECASE),
    re.compile(r"(?:ko'chasi|ko‘chasi|kuchasi|ko'cha|кўчаси|кўча|улица|ул\.):\s*([A-ZА-Яa-zа-яʻʼ'\d\s-]+)", re.IGNORECASE),
]

_MAHALLA_PATTERNS = [
    re.compile(r"([A-ZА-Яa-zа-яʻʼ'\d\s-]+?)\s*(?:mahallasi|mahalla|маҳалласи|маҳалла|махалла|mfy|m\.f\.y)", re.IGNORECASE),
]

_HOUSE_PATTERNS = [
    re.compile(r"(\d+[A-Za-zА-Яа-я]?)[ -]?(?:chi)?\s*(?:uy|dom|xonadon|дом|д\.|квартира|кв\.)", re.IGNORECASE),
    re.compile(r"(?:uy|dom|xonadon|дом|д\.|квартира|кв\.)[ -]?(\d+[A-Za-zА-Яа-я]?)", re.IGNORECASE),
    re.compile(r"(?:korpus|blok|корпус|блок)[ -]?(\d+)", re.IGNORECASE),
]

_ORIENTIR_PATTERNS = [
    re.compile(r"(?:mo'ljal|moljal|orientir|yaqinida|oldida|yonida|to'g'risida):\s*([A-Za-zА-Яа-яʻʼ'\d\s-]+)", re.IGNORECASE),
    re.compile(r"([A-Za-zА-Яа-яʻʼ'\d\s-]+?)\s+(?:oldida|yonida|yaqinida|ro'parasida)", re.IGNORECASE),
]


# Toshkent shahri 12 ta tumanining koordinata markazlari (GPS orqali avtomatik tuman aniqlash)
TASHKENT_DISTRICT_CENTROIDS = [
    ("Yunusobod tumani", 41.365, 69.285),
    ("Olmazor tumani", 41.350, 69.220),
    ("Mirzo Ulug'bek tumani", 41.335, 69.335),
    ("Shayxontohur tumani", 41.325, 69.235),
    ("Uchtepa tumani", 41.295, 69.170),
    ("Chilonzor tumani", 41.270, 69.205),
    ("Yakkasaroy tumani", 41.280, 69.250),
    ("Mirobod tumani", 41.290, 69.280),
    ("Yashnobod tumani", 41.295, 69.325),
    ("Sergeli tumani", 41.225, 69.230),
    ("Yangihayot tumani", 41.195, 69.210),
    ("Bektemir tumani", 41.230, 69.340),
]

_COORD_REGEX = re.compile(r"(?:q=|loc:|\b|\?)(-?\d{1,2}\.\d+)[,\s]+(-?\d{1,3}\.\d+)")


def find_district_by_coordinates(lat: float, lon: float) -> str | None:
    """Berilgan GPS kenglik (lat) va uzunlik (lon) bo'yicha Toshkent tumanini aniqlaydi."""
    # Toshkent atrofi koordinatalari (taxminan 41.05 - 41.50 lat, 69.05 - 69.50 lon)
    if 41.05 <= lat <= 41.50 and 69.05 <= lon <= 69.50:
        best_district = None
        min_dist_sq = float("inf")
        for dist_name, c_lat, c_lon in TASHKENT_DISTRICT_CENTROIDS:
            d_sq = (lat - c_lat) ** 2 + (lon - c_lon) ** 2
            if d_sq < min_dist_sq:
                min_dist_sq = d_sq
                best_district = dist_name
        if best_district:
            return f"Toshkent sh., {best_district}"
    return None


def extract_location(text: str) -> Tuple[str | None, str | None]:
    """Matndan shahar/tuman va aniq manzilni ajratib oladi.
    
    Qaytaradi:
        (district, address):
        district: Masalan, "Toshkent sh., Yunusobod tumani" yoki "Samarqand shahri"
        address: Masalan, "4-mavze, 12-uy" yoki "Navoiy ko'chasi, 24-uy"
    """
    if not text:
        return None, None

    clean_text = " ".join(text.split())
    lower_text = clean_text.lower()

    # 0. GPS koordinatalardan avtomatik shahar/tuman va ko'cha/uy manzilini aniqlash (Reverse Geocoding)
    coord_match = _COORD_REGEX.search(clean_text)
    geo_district = None
    geo_address = None
    if coord_match:
        try:
            c_lat = float(coord_match.group(1))
            c_lon = float(coord_match.group(2))
            geo_district, geo_address = reverse_geocode(c_lat, c_lon)
        except ValueError:
            pass

    # 1. Shahar va Tumanni aniqlash
    found_district = None
    is_tashkent = "toshkent" in lower_text or "tashkent" in lower_text

    for kw, dist_name in TASHKENT_DISTRICTS.items():
        if re.search(rf"\b{re.escape(kw)}(?:[a-zа-яʻʼ']{{1,7}})?\b", lower_text):
            found_district = f"Toshkent sh., {dist_name}"
            break

    if not found_district:
        # 1.1 Ko'cha yoki mavze nomi orqali tumanini aniqlash
        for street_kw, dist_name in TASHKENT_STREET_DISTRICT_MAP.items():
            if re.search(rf"\b{re.escape(street_kw)}(?:[a-zа-яʻʼ']{{1,7}})?\b", lower_text):
                found_district = f"Toshkent sh., {dist_name}"
                break

    if not found_district:
        for kw, city_name in OTHER_CITIES.items():
            if re.search(rf"\b{re.escape(kw)}(?:[a-zа-яʻʼ']{{1,7}})?\b", lower_text):
                found_district = city_name
                break

    # Agar matnda tuman nomi topilmagan bo'lsa, GPS orqali topilgan tumanni ishlatamiz
    if not found_district and geo_district:
        found_district = geo_district
    elif not found_district and is_tashkent:
        found_district = "Toshkent shahri"

    # 2. Aniq manzilni aniqlash (mavze, ko'cha, mahalla, uy)
    address_parts = []

    # Mavze / Kvartal
    for pat in _MAVZE_PATTERNS:
        m = pat.search(clean_text)
        if m:
            val = m.group(0).strip()
            if len(val) < 40 and val not in address_parts:
                address_parts.append(val)
                break

    # Ko'cha
    for pat in _STREET_PATTERNS:
        m = pat.search(clean_text)
        if m:
            val = m.group(1).strip() if m.lastindex else m.group(0).strip()
            # Tozalash
            val = re.sub(r"^(salom|iltimos|bizda|bizning|shu)\s+", "", val, flags=re.IGNORECASE)
            val = re.sub(
                r"^(toshkent|samarqand|buxoro|andijon|farg'ona|namangan|qarshi|yunusobod|chilonzor|"
                r"mirzo ulug'bek|sergeli|olmazor|uchtepa|mirobod|yashnobod|yakkasaroy|shayxontohur|"
                r"bektemir|yangihayot)\s+(?:shahar|shahri|tumani|tuman|t-ni)?\s*,?\s*",
                "", val, flags=re.IGNORECASE
            )
            val = re.sub(r"^\d+[ -]?(?:mavze|kvartal|massiv|daha)\s*,?\s*", "", val, flags=re.IGNORECASE)
            val = val.strip(", ")
            if not val.lower().endswith(("ko'chasi", "ko‘chasi", "ko'cha", "ko‘cha", "prospekti")):
                val = f"{val} ko'chasi"
            if len(val) < 60 and val not in address_parts:
                address_parts.append(val)
                break

    # Mahalla
    for pat in _MAHALLA_PATTERNS:
        m = pat.search(clean_text)
        if m:
            val = m.group(0).strip()
            val = re.sub(r"^(salom|iltimos|bizda|bizning)\s+", "", val, flags=re.IGNORECASE)
            if len(val) < 50 and val not in address_parts:
                address_parts.append(val)
                break

    # Uy / Dom
    for pat in _HOUSE_PATTERNS:
        m = pat.search(clean_text)
        if m:
            val = m.group(0).strip()
            if len(val) < 20 and val not in address_parts:
                address_parts.append(val)
                break

    # Orientir (agar mavze/ko'cha topilmagan bo'lsa)
    if not address_parts:
        for pat in _ORIENTIR_PATTERNS:
            m = pat.search(clean_text)
            if m:
                val = m.group(0).strip()
                if 5 < len(val) < 50:
                    address_parts.append(f"Mo'ljal: {val}")
                    break

    found_address = ", ".join(address_parts) if address_parts else None

    # Agar tuman topilmagan, lekin ko'chamizda/uyimizda deb yozilgan bo'lsa
    if not found_address and ("ko'cha" in lower_text or "uy" in lower_text or "mavze" in lower_text):
        # Qisqa ko'chirma
        for sentence in re.split(r"[.!?\n]", clean_text):
            s_low = sentence.lower()
            if any(k in s_low for k in ["ko'cha", "mavze", "kvartal", "dom", "uy oldi", "ko‘cha"]):
                s_strip = sentence.strip()
                if 5 < len(s_strip) <= 80:
                    found_address = s_strip
    if not found_address and geo_address:
        found_address = geo_address
    elif found_address and geo_address and not geo_address.startswith("GPS:"):
        # Agar matnda ham ko'cha/mavze bo'lsa va geocoding ham manzil topsa, boyitish
        if geo_address not in found_address:
            found_address = f"{found_address} ({geo_address})"

    return found_district, found_address

