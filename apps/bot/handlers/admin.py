"""Telegram bot administratorlari uchun handlerlar va statistika hisobotlari."""
import logging
from typing import Any

from aiogram import F, Router, types

from handlers.keyboards import get_admin_reply_keyboard, get_citizen_reply_keyboard
from handlers.state import ADMIN_SESSIONS, USER_PHONES, USER_ROLES
from services.backend_client import BackendClient


log = logging.getLogger("suvnazorat.bot.admin")
router = Router(name="admin")


def build_admin_summary_text(summary: dict[str, Any] | None) -> str:
    """Mas'ul xodimlar va administratorlar uchun ixcham tizim statistikasi."""
    if not summary:
        return "🛡️ <b>Mas'ul xodim / Admin Paneli</b>\n\n⚠️ Tizim statistikasi olinmadi."

    total = summary.get("total", 0)
    open_c = summary.get("open", 0)
    in_p = summary.get("in_progress", 0)
    res_c = summary.get("resolved", 0)
    sources_c = summary.get("sources_count", 0)
    recent = summary.get("recent", [])

    recent_lines = []
    for idx, inc in enumerate(recent[:5], 1):
        st_emoji = "🔴" if inc.get("status") == "OPEN" else "🟡" if inc.get("status") == "IN_PROGRESS" else "🟢"
        dist = inc.get("district") or "Toshkent sh."
        title = inc.get("title", "")[:40]
        recent_lines.append(f"{idx}. {st_emoji} <b>#{inc.get('id')}</b> {title} (📍 {dist})")

    recent_text = "\n".join(recent_lines) if recent_lines else "Hozircha yangi hodisalar yo'q."

    return (
        "🛡️ <b>SuvNazorat — Admin Boshqaruv Paneli</b>\n\n"
        "📊 <b>Markaziy Tizim Ko'rsatkichlari:</b>\n"
        f"• 📋 Jami hodisalar: <b>{total} ta</b>\n"
        f"• 🔴 Ochiq: <b>{open_c} ta</b>\n"
        f"• 🟡 Jarayonda: <b>{in_p} ta</b>\n"
        f"• 🟢 Hal qilingan: <b>{res_c} ta</b>\n"
        f"• 📡 Faol manbalar: <b>{sources_c} ta</b>\n\n"
        "🚨 <b>So'nggi hodisalar:</b>\n"
        f"{recent_text}\n\n"
        "🌐 Veb panel: http://localhost:3000/dashboard"
    )


@router.message(F.contact)
async def handle_contact_verification(
    message: types.Message,
    backend: BackendClient,
) -> None:
    """Telefon raqam yuborilganda adminlikni avtomatik aniqlash.
    
    Agar admin raqam bo'lsa: to'g'ridan-to'g'ri Admin paneli ochiladi.
    Aks holda: fuqaro rejimiga o'tadi va fuqaro menyusi ko'rsatiladi.
    Hech qanday qo'lda rol tanlash yoki so'rash mavjud emas.
    """
    user_id = message.from_user.id if message.from_user else message.chat.id
    contact = message.contact
    if not contact:
        return

    phone = contact.phone_number or ""
    if phone:
        USER_PHONES[user_id] = phone
    log.info("Foydalanuvchi kontakt yubordi: user_id=%s, phone=%s", user_id, phone)


    is_admin = await backend.check_admin(phone)
    if is_admin:
        USER_ROLES[user_id] = "ADMIN"
        ADMIN_SESSIONS.add(user_id)
        summary = await backend.get_summary()
        admin_text = build_admin_summary_text(summary)
        await message.reply(
            "✅ <b>Administratorlik muvaffaqiyatli tasdiqlandi!</b>\n\n"
            "Sizga SuvNazorat markaziy admin boshqaruv huquqlari berildi.",
            reply_markup=get_admin_reply_keyboard(),
            parse_mode="HTML",
        )
        await message.answer(admin_text, parse_mode="HTML")
    else:
        USER_ROLES[user_id] = "CITIZEN"
        await message.reply(
            "✅ <b>Raqamingiz qabul qilindi.</b>\n\n"
            "Suv ta'minoti bo'yicha murojaat, nosozlik haqida xabar, rasm yoki lokatsiyani shu yerga yuborishingiz mumkin.",
            reply_markup=get_citizen_reply_keyboard(),
            parse_mode="HTML",
        )


@router.message(F.text.in_({"📊 Markaziy Statistika", "🔄 Yangilash"}))
async def handle_admin_stats(
    message: types.Message,
    backend: BackendClient,
) -> None:
    """Adminlar uchun yangilangan markaziy statistika."""
    user_id = message.from_user.id if message.from_user else message.chat.id
    if USER_ROLES.get(user_id) != "ADMIN":
        return

    summary = await backend.get_summary()
    await message.reply(
        build_admin_summary_text(summary),
        reply_markup=get_admin_reply_keyboard(),
        parse_mode="HTML",
    )


@router.message(F.text == "🚨 So'nggi hodisalar")
async def handle_admin_recent_incidents(
    message: types.Message,
    backend: BackendClient,
) -> None:
    """Adminlar uchun so'nggi 10 ta hodisa ro'yxati."""
    user_id = message.from_user.id if message.from_user else message.chat.id
    if USER_ROLES.get(user_id) != "ADMIN":
        return

    summary = await backend.get_summary()
    recent = summary.get("recent", []) if summary else []
    if not recent:
        await message.reply("ℹ️ Hozircha yangi hodisalar mavjud emas.")
        return

    lines = ["🚨 <b>So'nggi hodisalar ro'yxati:</b>\n"]
    for inc in recent[:10]:
        st = inc.get("status")
        st_name = "Ochiq" if st == "OPEN" else "Jarayonda" if st == "IN_PROGRESS" else "Hal qilingan"
        st_icon = "🔴" if st == "OPEN" else "🟡" if st == "IN_PROGRESS" else "🟢"
        lines.append(
            f"• {st_icon} <b>#{inc.get('id')}</b> — {inc.get('title')}\n"
            f"  📍 <i>{inc.get('district') or 'Toshkent sh.'}</i> | Holati: <b>{st_name}</b>\n"
        )

    await message.reply(
        "\n".join(lines),
        reply_markup=get_admin_reply_keyboard(),
        parse_mode="HTML",
    )
