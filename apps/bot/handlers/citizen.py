"""Fuqarolar uchun bot butunlay yopilgan (o'chirilgan).

Shaxsiy chatdagi har qanday xabar (/start, matn, kontakt, rasm, video, lokatsiya) 
butunlay e'tiborsiz qoldiriladi va hech qanday javob qaytarilmaydi.
Bot faqat backend tizimi uchun Telegram kanallari va guruhlarini monitoring qilish vositasi sifatida xizmat qiladi.
"""
import logging
from aiogram import F, Router, types

log = logging.getLogger("suvnazorat.bot.citizen")
router = Router(name="citizen")


@router.message(F.chat.type == "private")
async def handle_private_chat_ignored(message: types.Message) -> None:
    """Fuqarolar uchun bot shaxsiy chatda butunlay o'chirilgan (start bosilsa ham javob bermaydi)."""
    log.debug("Shaxsiy chat xabari e'tiborsiz qoldirildi: user_id=%s", message.from_user.id if message.from_user else 0)
    return
