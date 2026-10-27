"""GPS koordinatalari bo'yicha shahar, tuman va aniq ko'cha/uy manzilini aniqlash servisi (Reverse Geocoding)."""
import logging
from typing import Tuple

import httpx

log = logging.getLogger("suvnazorat.geocoding")

# Toshkent shahri 12 ta tumanining koordinata markazlari (offline tuman aniqlash)
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

TASHKENT_DISTRICT_MAP = {
    "yunusobod": "Yunusobod tumani",
    "yunusabad": "Yunusobod tumani",
    "chilonzor": "Chilonzor tumani",
    "chilanzar": "Chilonzor tumani",
    "mirzo ulug'bek": "Mirzo Ulug'bek tumani",
    "mirzo-ulug'bek": "Mirzo Ulug'bek tumani",
    "yakkasaroy": "Yakkasaroy tumani",
    "yakkasaray": "Yakkasaroy tumani",
    "shayxontohur": "Shayxontohur tumani",
    "olmazor": "Olmazor tumani",
    "almazar": "Olmazor tumani",
    "uchtepa": "Uchtepa tumani",
    "sergeli": "Sergeli tumani",
    "mirobod": "Mirobod tumani",
    "mirabad": "Mirobod tumani",
    "yashnobod": "Yashnobod tumani",
    "bektemir": "Bektemir tumani",
    "yangihayot": "Yangihayot tumani",
    # Kirill / Ruscha
    "юнусабад": "Yunusobod tumani",
    "чиланзар": "Chilonzor tumani",
    "мирзо улугбек": "Mirzo Ulug'bek tumani",
    "яккасарай": "Yakkasaroy tumani",
    "шайхантахур": "Shayxontohur tumani",
    "алмазар": "Olmazor tumani",
    "учтепа": "Uchtepa tumani",
    "сергели": "Sergeli tumani",
    "мирабад": "Mirobod tumani",
    "яшнабад": "Yashnobod tumani",
    "бектемир": "Bektemir tumani",
    "янгихает": "Yangihayot tumani",
}

# Tezkor kesh (bir xil yoki juda yaqin koordinatalar qayta so'ralganda 0ms da javob berish uchun)
_GEO_CACHE: dict[tuple[float, float], Tuple[str | None, str | None]] = {}


def find_district_by_centroids(lat: float, lon: float) -> str | None:
    """Berilgan koordinatalarga eng yaqin Toshkent tumanini matematik aniqlash."""
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


def reverse_geocode(lat: float, lon: float) -> Tuple[str | None, str | None]:
    """GPS koordinatalaridan (lat, lon) shahar/tuman va aniq manzilni (ko'cha, mavze, uy) aniqlash.
    
    Qaytaradi:
        (district, address):
        district: "Toshkent sh., Yunusobod tumani"
        address: "Yunusobod-4 mavzesi, 8-uy" yoki "Amir Temur ko'chasi, 12-uy"
    """
    cache_key = (round(lat, 4), round(lon, 4))
    if cache_key in _GEO_CACHE:
        return _GEO_CACHE[cache_key]

    centroid_district = find_district_by_centroids(lat, lon)
    district = centroid_district
    address = None

    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        headers = {"User-Agent": "SuvNazorat/1.0 (info@suvnazorat.uz)"}
        params = {
            "lat": lat,
            "lon": lon,
            "format": "jsonv2",
            "accept-language": "uz,ru",
            "addressdetails": 1,
        }
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                addr = data.get("address", {})

                # 1. Tumanni aniqlash
                raw_district = (
                    addr.get("district")
                    or addr.get("suburb")
                    or addr.get("city_district")
                    or addr.get("county")
                    or ""
                )
                raw_dist_lower = raw_district.lower()

                for k, v in TASHKENT_DISTRICT_MAP.items():
                    if k in raw_dist_lower:
                        district = f"Toshkent sh., {v}"
                        break

                if not district:
                    city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("state")
                    if city:
                        district = f"{city} shahri" if "shahar" not in city.lower() else city

                # 2. Aniq manzil qismlari (mavze, mahalla, ko'cha, uy)
                parts = []
                road = addr.get("road")
                residential = addr.get("residential") or addr.get("neighbourhood") or addr.get("suburb")
                house_number = addr.get("house_number")
                mahalla = addr.get("village") or addr.get("hamlet") or addr.get("city")

                if residential and residential.lower() not in (district or "").lower():
                    res_clean = residential
                    if not any(w in res_clean.lower() for w in ["mavze", "kvartal", "mahalla", "massiv", "daha", "rayon"]):
                        res_clean = f"{res_clean} mavzesi"
                    parts.append(res_clean)
                elif mahalla and "mahalla" in mahalla.lower() and mahalla not in parts:
                    parts.append(mahalla)

                if road:
                    road_clean = road
                    if not any(w in road_clean.lower() for w in ["ko'cha", "ko‘cha", "ko'chasi", "ko‘chasi", "prospekt", "shoh", "улица"]):
                        road_clean = f"{road_clean} ko'chasi"
                    parts.append(road_clean)

                if house_number:
                    parts.append(f"{house_number}-uy")

                if not parts:
                    building = addr.get("amenity") or addr.get("building") or addr.get("office") or addr.get("shop")
                    if building:
                        parts.append(building)

                if parts:
                    address = ", ".join(parts)

    except Exception as e:
        log.warning("Reverse geocoding xatosi (%s, %s): %s", lat, lon, e)

    # Agar online aniqlanmagan bo'lsa, koordinatalarni chiroyli ko'rsatish
    if not address:
        address = f"GPS: {lat:.5f}, {lon:.5f}"

    res = (district, address)
    _GEO_CACHE[cache_key] = res
    return res
