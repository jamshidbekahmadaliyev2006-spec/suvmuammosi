"""Pytest test konfiguratsiyasi va fixturelar."""
import pytest

from config.settings import BotSettings


@pytest.fixture
def test_settings() -> BotSettings:
    return BotSettings(
        telegram_bot_token="test_token_123456",
        backend_url="http://testserver",
        telegram_bot_api_key="test_api_key_xyz",
        detection_rules_refresh_seconds=1,
        heartbeat_interval_seconds=1,
        app_env="test",
    )


@pytest.fixture
def sample_rules() -> list[dict]:
    return [
        {
            "id": 1,
            "name": "Quvur yorilishi",
            "keyword": "quvur yorildi",
            "category": "PIPE_BURST",
            "match_type": "PHRASE",
            "priority": 80,
            "is_active": True,
        },
        {
            "id": 2,
            "name": "Suv yo'qligi",
            "keyword": "suv yo'q",
            "category": "SUPPLY_OUTAGE",
            "match_type": "PHRASE",
            "priority": 70,
            "is_active": True,
        },
        {
            "id": 3,
            "name": "Kanalizatsiya avariyasi",
            "keyword": "kanalizatsiya",
            "category": "SEWAGE",
            "match_type": "WHOLE_WORD",
            "priority": 60,
            "is_active": True,
        },
        {
            "id": 4,
            "name": "Sizib chiqish",
            "keyword": "oqmoqda",
            "category": "LEAK",
            "match_type": "CONTAINS",
            "priority": 50,
            "is_active": True,
        },
    ]
