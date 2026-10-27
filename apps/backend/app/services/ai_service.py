"""Groq AI orqali Telegram xabarlarini intellektual tahlil qilish va saralash xizmati.

Fuqaro murojaatlari (shikoyat/avariya) va umumiy yangiliklar/rasmiy e'lonlarni
bir-biridan ajratadi, muammoning hal qilinganligini aniqlaydi va qisqa xulosa beradi.
"""
import hashlib
import json
import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.models.enums import IncidentCategory, Priority

logger = logging.getLogger("suvnazorat.ai")

# Tezkor xotira keshi (bir xil matnlarni qayta-qayta Groq'ga yubormaslik uchun)
_AI_CACHE: dict[str, dict[str, Any]] = {}


def _get_cache_key(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


SYSTEM_PROMPT = """Siz O'zbekistondagi SuvNazorat axborot tizimining yetakchi sun'iy intellekt (AI) tahlilchisisiz.
Sizga Telegram kanal va guruhlaridan kelgan xabar beriladi. Uni diqqat bilan o'rganing va quyidagi toifalardan biriga ajrating:

1. report_type (Xabar turi):
   - "ZAYAVKA": Aholi yoki fuqarolarning suv ta'minoti, quvur yorilishi, suv toshishi, oqova suv yoki boshqa muammo bo'yicha aniq shikoyati, murojaati yoki avariya arizasi.
   - "NEWS": OAV yoki kanallardagi umumiy yangilik, maqola, ob-havo ma'lumotlari, xorijiy xabarlar yoki boshqa axborotlar (Bu muammo emas!).
   - "GRATITUDE": Aholi tomonidan muammo hal qilingani uchun bildirilgan tashakkur, minnatdorchilik yoki rahmat (Masalan: "Rahmat, suv berildi", "Tuzatishdi").
   - "ANNOUNCEMENT": Suvsoz yoki hokimiyat tomonidan e'lon qilingan rejaviy ta'mirlash, suv vaqtincha to'xtatilishi yoki rasmiy ogohlantirishlar.
   - "IRRELEVANT": Reklama, kino, savdo, ish e'lonlari yoki suv tizimiga mutlaqo aloqador bo'lmagan postlar.

2. is_report (Real murojaat / arizami?):
   - true: Faqatgina fuqaro arizasi yoki tezkor chora ko'rilishi kerak bo'lgan real avariya (ZAYAVKA) bo'lsa.
   - false: Agar bu yangilik (NEWS), minnatdorchilik (GRATITUDE), e'lon (ANNOUNCEMENT) yoki reklama bo'lsa.

3. is_resolved (Muammo hal qilinganmi?):
   - true: Agar bu YANGILIK (NEWS), MINNATDORCHILIK (GRATITUDE), RASMIY E'LON (ANNOUNCEMENT) bo'lsa, YOKI ariza bartaraf etilgan bo'lsa (DOIMO true).
   - false: Faqatgina real ZAYAVKA bo'lib, muammo haligacha hal qilinmagan bo'lsa.

4. category (Kategoriya):
   - "PIPE_BURST": Quvur yorilishi / teshilishi / avariya.
   - "SUPPLY_OUTAGE": Suv ta'minoti yo'qligi / o'chirilganligi.
   - "LOW_PRESSURE": Suv bosimi pastligi / yetib bormasligi.
   - "LEAK": Tomchilab yoki oqib yotgan suv sizishi.
   - "FLOODING": Sel, yomg'ir suvi toshishi, ko'chani suv bosishi.
   - "SEWAGE": Kanalizatsiya / oqova suv toshishi yoki ifloslanishi.
   - "OTHER": Boshqa suv bilan bog'liq holatlar.

5. priority (Muhimlik darajasi):
   - "HIGH": Katta avariya, ko'chani suv bosishi, kasalxona/maktablar suvsiz qolishi.
   - "MEDIUM": Oddiy fuqaro murojaati yoki maishiy uzilish.
   - "LOW": Kichik nosozlik yoki umumiy axborot.

6. summary (Qisqa mazmun):
   - O'zbek tilida 1 ta aniq va lo'nda jumla bilan xabarning mohiyatini bayon qiling.

7. extracted_address (Manzil):
   - Xabarda tilga olingan aniq tuman, mavze, ko'cha yoki mahalla nomi (agar mavjud bo'lsa, aks holda null).

JAVOBNI FAQAT QUYIDAGI SOF JSON FORMATDA QAYTARING:
{
  "report_type": "ZAYAVKA" | "NEWS" | "GRATITUDE" | "ANNOUNCEMENT" | "IRRELEVANT",
  "is_report": true | false,
  "is_resolved": true | false,
  "category": "PIPE_BURST" | "SUPPLY_OUTAGE" | "LOW_PRESSURE" | "LEAK" | "FLOODING" | "SEWAGE" | "OTHER",
  "priority": "HIGH" | "MEDIUM" | "LOW",
  "summary": "...",
  "extracted_address": "..." | null
}"""


FALLBACK_MODELS = ["openai/gpt-oss-20b", "qwen/qwen3.8-27b", "openai/gpt-oss-120b"]


def analyze_text_with_groq(text: str, timeout_seconds: float = 8.0) -> dict[str, Any] | None:
    """Groq API orqali matnni tahlil qiladi va JSON ob'ekt qaytaradi."""
    settings = get_settings()
    if not settings.ai_analysis_enabled or not settings.groq_api_key:
        return None

    clean_text = text.strip()
    if len(clean_text) < 10:
        return None

    cache_key = _get_cache_key(clean_text)
    if cache_key in _AI_CACHE:
        return _AI_CACHE[cache_key]

    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }

    # Asosiy model va zaxira modellar
    primary_model = settings.groq_model or "openai/gpt-oss-20b"
    models_to_try = [primary_model] + [m for m in FALLBACK_MODELS if m != primary_model]

    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": clean_text[:2000]},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        try:
            with httpx.Client(timeout=timeout_seconds) as client:
                resp = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if resp.status_code == 429:
                    # Rate limit - keyingi modelga o'tish
                    logger.warning(f"Groq {model_name} rate limit (429), zaxira modelga o'tilmoqda...")
                    continue
                if resp.status_code != 200:
                    logger.warning(f"Groq API {model_name} javob kodi: {resp.status_code}")
                    continue

                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                result = json.loads(content)

                # Validatsiya va normallashtirish
                report_type = result.get("report_type", "ZAYAVKA").upper()
                if report_type in ("MUROJAAT", "ZAYAVKA", "APPL"):
                    report_type = "ZAYAVKA"
                elif report_type in ("YANGILIK", "NEWS"):
                    report_type = "NEWS"
                elif report_type in ("TASHAKKUR", "GRATITUDE", "MINNATDORCHILIK"):
                    report_type = "GRATITUDE"
                elif report_type in ("RASMIY_ELON", "ANNOUNCEMENT", "ELON"):
                    report_type = "ANNOUNCEMENT"
                elif report_type in ("IRRELEVANT", "REKLAMA", "SPAM"):
                    report_type = "IRRELEVANT"
                else:
                    report_type = "ZAYAVKA" if result.get("is_report") else "NEWS"

                result["report_type"] = report_type
                # Yangilik, minnatdorchilik va rasmiy e'lonlar hech qachon OPEN bo'lmaydi!
                if report_type in ("NEWS", "GRATITUDE", "ANNOUNCEMENT", "IRRELEVANT"):
                    result["is_resolved"] = True

                if len(_AI_CACHE) > 1000:
                    _AI_CACHE.clear()
                _AI_CACHE[cache_key] = result
                return result
        except Exception as e:
            logger.warning(f"Groq {model_name} tahlilida xatolik: {e}")
            continue

    return None


def get_heuristic_fallback(text: str) -> dict[str, Any]:
    """Internet yoki API bo'lmaganda tezkor evristik tahlil."""
    low = text.lower()
    
    # 1. Reklama / kinolar / savdo
    if any(k in low for k in ("kino", "akula", "doshirak", "compass mall", "ishga taklif", "super narxlar", "chegirma", "hovli sotiladi", "savdo vakillari", "narxlari aynan siz uchun")):
        return {
            "report_type": "IRRELEVANT",
            "is_report": False,
            "is_resolved": True,
            "category": "OTHER",
            "priority": "LOW",
            "summary": "Mavzuga aloqasiz xabar / reklama",
            "extracted_address": None,
        }

    # 2. Minnatdorchilik / Tashakkur
    if any(k in low for k in ("rahmat", "katta rahmat", "миннатдор", "ташаккур", "спасибо", "tashakkur", "tuzatib berishdi", "suv berildi rahmat")):
        return {
            "report_type": "GRATITUDE",
            "is_report": False,
            "is_resolved": True,
            "category": "OTHER",
            "priority": "LOW",
            "summary": "Muammo hal etilgani uchun minnatdorchilik xabari",
            "extracted_address": None,
        }

    # 3. Rasmiy e'lon kalitlari
    if any(k in low for k in ("reja asosida", "rejali", "diqqat", "ogohlantirish", "вақтинча тўхтатилади", "vaqtincha to'xtatiladi", "эълон", "e'lon")):
        return {
            "report_type": "ANNOUNCEMENT",
            "is_report": False,
            "is_resolved": True,
            "category": "SUPPLY_OUTAGE",
            "priority": "LOW",
            "summary": "Suv ta'minoti bo'yicha rasmiy ogohlantirish / e'lon",
            "extracted_address": None,
        }

    # 4. Fuqaro arizasi / shikoyati / avariya
    is_complaint = any(k in low for k in ("murojaat", "shikoyat", "aholi", "fuqaro:", "fuqaro murojaati", "suv yo'q", "suv yoq", "quvur yorildi", "oqib yotibdi", "kelmadi", "chora ko'rilmadi", "ёрдам", "мурожаат")) and not any(k in low for k in ("makkada", "saudiya", "britaniyada", "xitoyda", "rossiyada", "saylov", "nani", "shomurodov", "prezident", "qasddan", "sud", "qamoqxona"))

    if is_complaint:
        is_res = any(k in low for k in ("hal qilindi", "bartaraf etildi", "tuzatildi", "ta'mirlandi", "устранено", "починили"))
        return {
            "report_type": "ZAYAVKA",
            "is_report": True,
            "is_resolved": is_res,
            "category": "PIPE_BURST" if "quvur" in low else ("SUPPLY_OUTAGE" if "suv yo" in low else "OTHER"),
            "priority": "HIGH" if "tosh" in low or "quvur" in low else "MEDIUM",
            "summary": text.strip().split("\n")[0][:120],
            "extracted_address": None,
        }

    # 5. Qolganlari OAV va yangiliklar (hech qachon hal qilinmagan qizil holatda bo'lmaydi!)
    return {
        "report_type": "NEWS",
        "is_report": False,
        "is_resolved": True,
        "category": "OTHER",
        "priority": "LOW",
        "summary": text.strip().split("\n")[0][:120],
        "extracted_address": None,
    }
