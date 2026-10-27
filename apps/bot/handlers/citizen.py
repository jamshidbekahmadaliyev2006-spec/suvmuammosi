"""Telegram bot fuqarolar rejimi: murojaatlar, lokatsiya, foto, video va matnli xabarlar."""
import logging

from aiogram import F, Router, types

from handlers.keyboards import (
    get_admin_reply_keyboard,
    get_cancel_inline_keyboard,
    get_citizen_reply_keyboard,
    get_phone_request_keyboard,
)
from handlers.processor import process_telegram_message
from handlers.state import ADMIN_SESSIONS, LAST_USER_INCIDENTS, USER_ROLES
from services.backend_client import BackendClient
from services.deduplicator import MessageDeduplicator
from services.rules_cache import RulesCache

log = logging.getLogger("suvnazorat.bot.citizen")
router = Router(name="citizen")


@router.message(F.text.in_({"/start", "/help", "🔄 Bosh menyu"}))
async def handle_start_command(message: types.Message) -> None:
    """Botni boshlash yoki qayta yuklash."""
    user_id = message.from_user.id if message.from_user else message.chat.id

    # Agar allaqachon admin bo'lsa
    if user_id in ADMIN_SESSIONS or USER_ROLES.get(user_id) == "ADMIN":
        await message.reply(
            "Assalomu alaykum! Administrator boshqaruv paneli faol.",
            reply_markup=get_admin_reply_keyboard(),
        )
        return

    # Agar fuqaro sifatida tanilgan bo'lsa
    if USER_ROLES.get(user_id) == "CITIZEN":
        welcome_text = (
            "Assalomu alaykum!\n\n"
            "Suv ta'minoti bo'yicha murojaat yoki nosozlik haqida xabar, manzil, rasm yoki lokatsiyani shu yerga yuborishingiz mumkin."
        )
        await message.reply(
            welcome_text,
            reply_markup=get_citizen_reply_keyboard(),
        )
        return

    # Yangi foydalanuvchi: telefon raqam so'raladi
    welcome_prompt = (
        "Assalomu alaykum!\n\n"
        "Suv ta'minoti bo'yicha murojaat yuborish uchun pastdagi «📱 Telefon raqamni yuborish» tugmasini bosing."
    )
    await message.reply(
        welcome_prompt,
        reply_markup=get_phone_request_keyboard(),
    )


@router.message(F.text.in_({"✍️ Murojaat yo'llash", "✍️ Yangi murojaat yo'llash", "/murojaat"}))
async def handle_new_appeal(message: types.Message) -> None:
    """Yangi murojaat yo'llash yo'riqnomasi."""
    await message.reply(
        "Muammo haqida ma'lumot, manzil, rasm yoki lokatsiya yuborishingiz mumkin.",
        reply_markup=get_citizen_reply_keyboard(),
    )


@router.message(F.text.in_({"ℹ️ Bot haqida", "/status"}))
async def handle_bot_info(
    message: types.Message,
    cache: RulesCache,
) -> None:
    """Bot haqida qisqa ma'lumot."""
    await message.reply(
        "💧 SuvNazorati — Toshkent shahri suv ta'minoti va avariyalarni nazorat qilish tizimi.",
        reply_markup=get_citizen_reply_keyboard(),
    )


@router.message(F.text == "/ping")
async def handle_ping(message: types.Message) -> None:
    """Aloqa tekshiruvi."""
    await message.reply("pong!")


# ===================== Murojaatni Bekor Qilish =====================

@router.callback_query(F.data.startswith("cancel_inc:"))
async def handle_cancel_inline(
    callback: types.CallbackQuery,
    backend: BackendClient,
) -> None:
    """Inline tugma orqali murojaatni bekor qilish."""
    data = callback.data or ""
    parts = data.split(":")
    if len(parts) >= 2 and parts[1].isdigit():
        inc_id = int(parts[1])
        chat_id = callback.message.chat.id if callback.message else 0
        user_id = callback.from_user.id if callback.from_user else chat_id
        await backend.cancel_incident(inc_id, chat_id)
        if LAST_USER_INCIDENTS.get(user_id) == inc_id:
            LAST_USER_INCIDENTS.pop(user_id, None)

    await callback.answer("Murojaat bekor qilindi.")
    if callback.message:
        try:
            await callback.message.edit_text(
                "❌ <b>Murojaatingiz bekor qilindi.</b>",
                parse_mode="HTML",
            )
        except Exception:
            pass


@router.message(F.text.in_({"❌ Bekor qilish", "❌ Murojaatni bekor qilish", "/cancel", "bekor qilish", "Bekor qilish"}))
async def handle_cancel_message(
    message: types.Message,
    backend: BackendClient,
) -> None:
    """Xabar yoki klaviatura orqali oxirgi murojaatni bekor qilish."""
    user_id = message.from_user.id if message.from_user else message.chat.id
    last_inc_id = LAST_USER_INCIDENTS.get(user_id)

    if last_inc_id:
        await backend.cancel_incident(last_inc_id, message.chat.id)
        LAST_USER_INCIDENTS.pop(user_id, None)
        await message.reply(
            "❌ <b>Murojaatingiz bekor qilindi.</b>",
            reply_markup=get_citizen_reply_keyboard(),
            parse_mode="HTML",
        )
    else:
        await message.reply(
            "Bekor qilinadigan faol murojaat topilmadi.",
            reply_markup=get_citizen_reply_keyboard(),
        )


# ===================== Lokatsiya, Foto, Video, Matn =====================

@router.message(F.location)
async def handle_location_message(
    message: types.Message,
    cache: RulesCache,
    backend: BackendClient,
    dedup: MessageDeduplicator,
) -> None:
    """Foydalanuvchi GPS lokatsiya yuborganda."""
    user_id = message.from_user.id if message.from_user else message.chat.id

    resp = await process_telegram_message(message, cache, backend, dedup, is_citizen=True)
    inc_id = resp.get("incident_id") if resp else None
    district = resp.get("district") if resp else None
    address = resp.get("address") if resp else None

    if inc_id:
        LAST_USER_INCIDENTS[user_id] = inc_id

    loc_str = ", ".join(filter(None, [district, address]))
    addr_info = f"\n📍 <b>Aniqlangan manzil:</b> {loc_str}" if loc_str else ""

    inline_kb = get_cancel_inline_keyboard(inc_id)
    await message.reply(
        f"✅ <b>Lokatsiya qabul qilindi.</b>{addr_info}",
        reply_markup=inline_kb,
        parse_mode="HTML",
    )



@router.message(F.photo)
async def handle_photo_message(
    message: types.Message,
    cache: RulesCache,
    backend: BackendClient,
    dedup: MessageDeduplicator,
) -> None:
    """Foydalanuvchi rasm yuborganda."""
    user_id = message.from_user.id if message.from_user else message.chat.id

    resp = await process_telegram_message(message, cache, backend, dedup, is_citizen=True)
    inc_id = resp.get("incident_id") if resp else None
    if inc_id:
        LAST_USER_INCIDENTS[user_id] = inc_id

    inline_kb = get_cancel_inline_keyboard(inc_id)
    await message.reply(
        "✅ <b>Rasm qabul qilindi.</b>",
        reply_markup=inline_kb,
        parse_mode="HTML",
    )


@router.message(F.video)
async def handle_video_message(
    message: types.Message,
    cache: RulesCache,
    backend: BackendClient,
    dedup: MessageDeduplicator,
) -> None:
    """Foydalanuvchi video yuborganda."""
    user_id = message.from_user.id if message.from_user else message.chat.id

    resp = await process_telegram_message(message, cache, backend, dedup, is_citizen=True)
    inc_id = resp.get("incident_id") if resp else None
    if inc_id:
        LAST_USER_INCIDENTS[user_id] = inc_id

    inline_kb = get_cancel_inline_keyboard(inc_id)
    await message.reply(
        "✅ <b>Video qabul qilindi.</b>",
        reply_markup=inline_kb,
        parse_mode="HTML",
    )


@router.message(F.chat.type == "private")
async def handle_private_text_report(
    message: types.Message,
    cache: RulesCache,
    backend: BackendClient,
    dedup: MessageDeduplicator,
) -> None:
    """Shaxsiy chatda fuqaro yoki admin matnli murojaat yozganda."""
    user_id = message.from_user.id if message.from_user else message.chat.id

    resp = await process_telegram_message(message, cache, backend, dedup, is_citizen=True)
    inc_id = resp.get("incident_id") if resp else None
    if inc_id:
        LAST_USER_INCIDENTS[user_id] = inc_id

    inline_kb = get_cancel_inline_keyboard(inc_id)
    await message.reply(
        "✅ <b>Qabul qilindi.</b>",
        reply_markup=inline_kb,
        parse_mode="HTML",
    )
