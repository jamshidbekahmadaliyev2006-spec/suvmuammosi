"""Telegram bot handlerlarining asosiy agregatori va tashqi interfeysi.

Ushbu modul bot arxitekturasini toza va modulli saqlash maqsadida handlerlarni
alohida ixtisoslashgan fayllarga ajratadi:
- keyboards.py: barcha menyu va klaviaturalar
- state.py: foydalanuvchi rollari va admin sessiyalari
- processor.py: xabarlarni tahlil qilish, media ajratish va backendga uzatish
- admin.py: adminlikni tekshirish, admin paneli va tizim statistikasi
- citizen.py: fuqarolar murojaatlari, GPS lokatsiya, foto/video yuborish
- group_channel.py: Telegram guruhlari va kanallari monitoringi
"""

from aiogram import Router

from handlers.admin import build_admin_summary_text, router as admin_router
from handlers.citizen import router as citizen_router
from handlers.group_channel import router as group_channel_router
from handlers.keyboards import (
    get_admin_reply_keyboard,
    get_cancel_inline_keyboard,
    get_citizen_reply_keyboard,
    get_phone_request_keyboard,
)
from handlers.processor import process_telegram_message
from handlers.state import ADMIN_SESSIONS, LAST_USER_INCIDENTS, USER_ROLES

# Asosiy router: barcha ixtisoslashgan routerlarni birlashtiradi
router = Router(name="messages")
router.include_router(group_channel_router)
router.include_router(admin_router)
router.include_router(citizen_router)

__all__ = [
    "ADMIN_SESSIONS",
    "LAST_USER_INCIDENTS",
    "USER_ROLES",
    "build_admin_summary_text",
    "get_admin_reply_keyboard",
    "get_cancel_inline_keyboard",
    "get_citizen_reply_keyboard",
    "get_phone_request_keyboard",
    "process_telegram_message",
    "router",
]
