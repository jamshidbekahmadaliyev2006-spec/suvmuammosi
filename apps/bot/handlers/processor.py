"""Telegram xabarlarini tahlil qilish, media ajratish va backendga uzatish servisi."""
import logging
from datetime import UTC
from typing import Any

from aiogram import types

from handlers.state import USER_PHONES
from services.backend_client import BackendClient
from services.deduplicator import MessageDeduplicator
from services.geocoding import reverse_geocode_async
from services.matcher import match_message
from services.rules_cache import RulesCache

log = logging.getLogger("suvnazorat.bot.processor")


def _extract_media(message: types.Message) -> tuple[str | None, str | None]:
    """Keraksiz katta faylni yuklab olmasdan turi va file_id sini aniqlaydi."""
    if message.photo:
        return "photo", message.photo[-1].file_id
    if message.video:
        return "video", message.video.file_id
    if message.location:
        return "location", f"{message.location.latitude},{message.location.longitude}"
    if message.document:
        return "document", message.document.file_id
    return None, None


def _build_message_url(
    chat: types.Chat,
    message_id: int,
    thread_id: int | None = None,
) -> str | None:
    """Xabarga to'g'ridan-to'g'ri havolani shakllantirish.
    
    Agar xabar guruhdagi alohida chatda (forum mavzusi/topic) yozilgan bo'lsa,
    havola to'g'ridan-to'g'ri o'sha mavzuga (/topic_id/message_id) olib boradi.
    """
    chat_username = chat.username
    chat_str = str(chat.id)
    cid = chat_str[4:] if chat_str.startswith("-100") else chat_str.lstrip("-")

    # Forum guruhi yoki mavzudagi (topic/thread) xabar bo'lsa
    if thread_id and thread_id != message_id:
        if chat_username:
            return f"https://t.me/{chat_username}/{thread_id}/{message_id}"
        return f"https://t.me/c/{cid}/{thread_id}/{message_id}"

    if chat_username:
        return f"https://t.me/{chat_username}/{message_id}"
    if chat_str.startswith("-"):
        return f"https://t.me/c/{cid}/{message_id}"
    return None


async def process_telegram_message(
    message: types.Message,
    cache: RulesCache,
    backend: BackendClient,
    dedup: MessageDeduplicator,
    is_citizen: bool = False,
) -> dict[str, Any] | None:
    """Xabarni tahlil qilish va backendga uzatishning asosiy mantiqi.
    
    Muhim: Guruh, kanal yoki shaxsiy chatdan kelgan hech bir murojaat tashlab ketilmaydi.
    """
    chat = message.chat
    message_id = message.message_id
    chat_id = chat.id

    # 1. Takroriy xabarlarni tekshirish
    if await dedup.is_duplicate(chat_id, message_id):
        log.debug("Takroriy xabar o'tkazib yuborildi: chat_id=%s, msg_id=%s", chat_id, message_id)
        return None

    # 2. Xabar matnini aniqlash va GPS manzilini boyitish
    text = (message.text or message.caption or "").strip()
    has_loc = message.location and isinstance(getattr(message.location, "latitude", None), (int, float))
    if has_loc:
        lat = float(message.location.latitude)
        lon = float(message.location.longitude)

        dist, addr = await reverse_geocode_async(lat, lon)
        loc_str = ", ".join(filter(None, [dist, addr]))
        loc_info = f"📍 Manzil: {loc_str}\n" if loc_str else ""
        coords_str = f"GPS: {lat:.5f}, {lon:.5f}"
        if text:
            text = f"{text}\n{coords_str}\n{loc_info}🗺 Google Xarita: https://maps.google.com/?q={lat},{lon}"
        else:
            text = f"GPS Lokatsiya ({coords_str})\n{loc_info}🗺 Google Xarita: https://maps.google.com/?q={lat},{lon}"
    elif not text:
        if message.photo:
            text = "Hodisa joyidan olingan fotosurat"
        elif message.video:
            text = "Hodisa joyidan olingan video xabar"
        else:
            log.debug("Bo'sh matnli xabar o'tkazib yuborildi: msg_id=%s", message_id)
            return None


    # 3. Media va manba ma'lumotlari
    media_type, file_id = _extract_media(message)

    # Agar xabar kanaldan forward qilingan bo'lsa (aiogram 3 forward tekshiruvi)
    forward_chat = getattr(message, "forward_from_chat", None)
    forward_msg_id = getattr(message, "forward_from_message_id", None)
    if not forward_chat and hasattr(message, "forward_origin"):
        origin = message.forward_origin
        if getattr(origin, "type", None) == "channel" and hasattr(origin, "chat"):
            forward_chat = origin.chat
            forward_msg_id = getattr(origin, "message_id", None)

    if forward_chat:
        chat_id = forward_chat.id
        chat_title = getattr(forward_chat, "title", None) or f"Kanal {forward_chat.id}"
        chat_username = getattr(forward_chat, "username", None)
        chat_type = "CHANNEL"
        actual_msg_id = forward_msg_id or message_id
        forward_thread_id = getattr(forward_chat, "message_thread_id", None)
        message_url = _build_message_url(forward_chat, actual_msg_id, forward_thread_id)
        is_citizen = False
    else:
        # Topic / Thread ID (guruhdagi alohida yozilgan chat yoki forum mavzusi)
        thread_id = getattr(message, "message_thread_id", None)
        message_url = _build_message_url(chat, message_id, thread_id)
        chat_type = "CHANNEL" if chat.type == "channel" else "GROUP"
        chat_title = getattr(chat, "title", None) or getattr(chat, "full_name", None) or f"Telegram {chat_id}"
        chat_username = getattr(chat, "username", None)

    msg_date = message.date
    if msg_date.tzinfo is None:
        msg_date = msg_date.replace(tzinfo=UTC)

    user_id = message.from_user.id if message.from_user else chat_id
    sender_phone = USER_PHONES.get(user_id) or (message.contact.phone_number if message.contact else None)
    sender_name = message.from_user.full_name if message.from_user else None

    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "chat_title": chat_title,
        "chat_username": chat_username,
        "chat_type": chat_type,
        "text": text,
        "timestamp": msg_date.isoformat(),
        "message_url": message_url,
        "media_type": media_type,
        "file_id": file_id,
        "is_citizen_report": is_citizen,
        "sender_phone": sender_phone,
        "sender_name": sender_name,
    }

    # Manbani faqat haqiqiy guruh yoki kanallar uchun ro'yxatga olamiz (fuqarolar guruhlarga aralashmaydi)
    if not is_citizen and chat.type in ("group", "supergroup", "channel"):
        try:
            await backend.register_source(
                chat_id=chat_id,
                chat_title=chat_title,
                chat_username=payload["chat_username"],
                source_type=chat_type,
            )
        except Exception as e:
            log.debug("register_source xatosi: %s", e)


    # Backendga yuborish (Dashboard va Hodisalar ro'yxatiga tushadi)
    resp = await backend.send_message(payload)
    if resp:
        log.info(
            "Xabar backendga yetkazildi: status=%s, incident_id=%s, chat_id=%s",
            resp.get("status"),
            resp.get("incident_id"),
            chat_id,
        )
    return resp
