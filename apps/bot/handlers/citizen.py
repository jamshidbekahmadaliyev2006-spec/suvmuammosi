"""Telegram bot shaxsiy chat handlerlari.

ESLATMA: Tizim talabiga ko'ra, bot orqali to'g'ridan-to'g'ri murojaat qabul qilinmaydi.
Monitoring faqat ruxsat etilgan Telegram kanallari va guruhlaridagi postlar orqali amalga oshiriladi.
"""
import logging

from aiogram import F, Router, types

from handlers.keyboards import get_admin_reply_keyboard
from handlers.state import ADMIN_SESSIONS, USER_ROLES

log = logging.getLogger("suvnazorat.bot.citizen")
router = Router(name="citizen")

NOTICE_TEXT = (
    "⚠️ <b>Ushbu bot fuqarolardan to'g'ridan-to'g'ri murojaat qabul qilmaydi.</b>\n\n"
    "Tizim suv ta'minoti va avariyalar bo'yicha xabarlarni faqat rasmiy <b>Telegram kanallari va guruhlaridan</b> "
    "avtomatik monitoring qilish uchun ishlaydi."
)


@router.message(F.chat.type == "private", F.text.in_({"/start", "/help", "🔄 Bosh menyu"}))
async def handle_start_command(message: types.Message) -> None:
    """Bot boshlanganda foydalanuvchini ogohlantirish."""
    user_id = message.from_user.id if message.from_user else message.chat.id

    # Agar administrator bo'lsa, admin panelini ko'rsatish
    if user_id in ADMIN_SESSIONS or USER_ROLES.get(user_id) == "ADMIN":
        await message.reply(
            "Assalomu alaykum! Administrator boshqaruv paneli faol.",
            reply_markup=get_admin_reply_keyboard(),
        )
        return

    # Oddiy foydalanuvchilar uchun botdan murojaat yuborish imkoni yo'qligi haqida xabar
    await message.reply(
        NOTICE_TEXT,
        reply_markup=types.ReplyKeyboardRemove(),
        parse_mode="HTML",
    )


@router.message(F.chat.type == "private", F.text == "/ping")
async def handle_ping(message: types.Message) -> None:
    """Aloqa tekshiruvi."""
    await message.reply("pong!")


@router.message(F.chat.type == "private")
async def handle_all_private_messages(message: types.Message) -> None:
    """Shaxsiy chatga yuborilgan har qanday xabar, rasm, video yoki lokatsiyaga rad javobini qaytarish."""
    user_id = message.from_user.id if message.from_user else message.chat.id

    if user_id in ADMIN_SESSIONS or USER_ROLES.get(user_id) == "ADMIN":
        # Adminlar xabarlarini admin paneli handlerlari boshqaradi
        return

    await message.reply(
        NOTICE_TEXT,
        reply_markup=types.ReplyKeyboardRemove(),
        parse_mode="HTML",
    )
