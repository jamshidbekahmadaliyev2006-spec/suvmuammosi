"""Telegram guruhlar va kanallardagi xabarlarni monitoring qilish handlerlari."""
import logging

from aiogram import F, Router, types

from handlers.processor import process_telegram_message
from services.backend_client import BackendClient
from services.deduplicator import MessageDeduplicator
from services.rules_cache import RulesCache

log = logging.getLogger("suvnazorat.bot.group_channel")
router = Router(name="group_channel")


@router.my_chat_member()
async def handle_bot_membership_update(
    event: types.ChatMemberUpdated,
    backend: BackendClient,
) -> None:
    """Bot yangi guruh yoki kanalga qo'shilganda manbani avtomatik ro'yxatga oladi."""
    new_status = event.new_chat_member.status
    if new_status in ("member", "administrator"):
        chat = event.chat
        chat_type = "CHANNEL" if chat.type == "channel" else "GROUP"
        title = chat.title or chat.full_name or f"Telegram {chat.id}"
        await backend.register_source(
            chat_id=chat.id,
            chat_title=title,
            chat_username=chat.username,
            source_type=chat_type,
        )
        if chat.type in ("group", "supergroup"):
            try:
                await event.bot.send_message(
                    chat.id,
                    "💧 <b>SuvNazorat monitoring tizimi ulandi.</b>\n"
                    "Guruhdagi suv ta'minoti va avariyalar haqidagi xabarlar markaziy boshqaruvga uzatiladi.",
                    parse_mode="HTML",
                )
            except Exception:
                pass


@router.channel_post()
async def handle_channel_post(
    message: types.Message,
    cache: RulesCache,
    backend: BackendClient,
    dedup: MessageDeduplicator,
) -> None:
    """Kanalga chiqarilgan postlarni tahlil qiladi va dashboardga uzatadi."""
    await process_telegram_message(message, cache, backend, dedup, is_citizen=False)


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group_message(
    message: types.Message,
    cache: RulesCache,
    backend: BackendClient,
    dedup: MessageDeduplicator,
) -> None:
    """Telegram guruhlaridagi xabarlarni qabul qilish va backendga uzatish."""
    # Guruhga yangi a'zo qo'shilganda
    if message.new_chat_members:
        bot_user = await message.bot.get_me()
        if any(m.id == bot_user.id for m in message.new_chat_members):
            title = message.chat.title or message.chat.full_name or f"Telegram {message.chat.id}"
            await backend.register_source(
                chat_id=message.chat.id,
                chat_title=title,
                chat_username=message.chat.username,
                source_type="GROUP",
            )
            return

    # Guruhdagi barcha xabarlarni qayta ishlash
    await process_telegram_message(message, cache, backend, dedup, is_citizen=False)
