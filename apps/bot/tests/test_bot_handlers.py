from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from config.settings import BotSettings
from handlers.messages import process_telegram_message
from services.deduplicator import MessageDeduplicator


@pytest.mark.asyncio
async def test_process_telegram_message_flow():
    # 1. Soxta Message obyekti
    msg = MagicMock()
    msg.message_id = 999
    msg.chat.id = -100123456789
    msg.chat.type = "channel"
    msg.chat.title = "Suv Ta'minoti Kanali"
    msg.chat.username = "suv_kanali"
    msg.text = "Diqqat! Ko'chada katta quvur yorildi!"
    msg.caption = None
    msg.photo = None
    msg.video = None
    msg.document = None
    msg.date = datetime.now(UTC)

    # 2. Servislar
    cache = MagicMock()
    cache.rules = [
        {"id": 1, "keyword": "quvur yorildi", "category": "PIPE_BURST", "match_type": "PHRASE", "priority": 80}
    ]

    backend = MagicMock()
    backend.send_message = AsyncMock(return_value={"status": "INCIDENT_CREATED", "incident_id": 101})

    dedup = MessageDeduplicator()

    # Birinchi marta: xabar qabul qilinadi va backendga uzatiladi
    resp = await process_telegram_message(msg, cache, backend, dedup)
    assert resp is not None
    assert resp["incident_id"] == 101
    assert backend.send_message.call_count == 1

    # Ikkinchi marta: aynan shu xabar kelsa, deduplicator uni qaytaradi, backend chaqirilmaydi
    backend.send_message.reset_mock()
    resp2 = await process_telegram_message(msg, cache, backend, dedup)
    assert resp2 is None
    assert backend.send_message.call_count == 0


def test_bot_settings_validation():
    # Token yoki API kaliti bo'lmaganda startda xatolik berishi kerak
    settings = BotSettings(telegram_bot_token="", telegram_bot_api_key="", app_env="production")
    with pytest.raises(ValueError):
        settings.validate_for_start()


@pytest.mark.asyncio
async def test_process_location_message_reverse_geocodes():
    msg = MagicMock()
    msg.message_id = 1001
    msg.chat.id = 555666777
    msg.chat.type = "private"
    msg.chat.title = "Ali Valiyev"
    msg.chat.username = "alivali"
    msg.text = None
    msg.caption = None
    msg.photo = None
    msg.video = None
    msg.document = None
    msg.date = datetime.now(UTC)

    # Set valid location coordinates (Yunusobod)
    msg.location = MagicMock()
    msg.location.latitude = 41.365
    msg.location.longitude = 69.285

    cache = MagicMock()
    cache.rules = []
    backend = MagicMock()
    backend.send_message = AsyncMock(
        return_value={
            "status": "INCIDENT_CREATED",
            "incident_id": 202,
            "district": "Toshkent sh., Yunusobod tumani",
            "address": "Yunusobod-4 mavzesi, 8-uy",
        }
    )
    dedup = MessageDeduplicator()

    resp = await process_telegram_message(msg, cache, backend, dedup, is_citizen=True)
    assert resp is not None
    assert resp["incident_id"] == 202

    # Verify sent payload contains reverse geocoded information
    payload = backend.send_message.call_args[0][0]
    assert "GPS" in payload["text"]
    assert "maps.google.com" in payload["text"]
    assert payload["media_type"] == "location"

