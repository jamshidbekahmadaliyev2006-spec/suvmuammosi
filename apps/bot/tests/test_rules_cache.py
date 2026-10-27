import httpx
import pytest

from services.rules_cache import RulesCache


@pytest.mark.asyncio
async def test_rules_cache_fetch_success(monkeypatch):
    cache = RulesCache(
        backend_url="http://testbackend",
        api_key="bot_secret_key",
        refresh_interval=1,
    )

    mock_response = {
        "version": 42,
        "rules": [
            {
                "id": 10,
                "name": "Quvur yorildi",
                "keyword": "quvur yorildi",
                "category": "PIPE_BURST",
                "match_type": "PHRASE",
                "priority": 80,
            }
        ],
    }

    async def mock_get(self, url, headers=None, timeout=None):
        return httpx.Response(200, json=mock_response)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    success = await cache.fetch_rules()
    assert success is True
    assert cache.rules_loaded is True
    assert cache.version == 42
    assert len(cache.rules) == 1
    assert cache.rules[0]["keyword"] == "quvur yorildi"
    assert cache.is_stale is False


@pytest.mark.asyncio
async def test_rules_cache_version_update_without_restart(monkeypatch):
    cache = RulesCache(
        backend_url="http://testbackend",
        api_key="bot_secret_key",
        refresh_interval=1,
    )

    # 1-holat: 1-versiya
    async def mock_get_v1(self, url, headers=None, timeout=None):
        if "version" in str(url):
            return httpx.Response(200, json={"version": 1})
        return httpx.Response(
            200,
            json={
                "version": 1,
                "rules": [{"id": 1, "keyword": "suv yo'q", "priority": 50}],
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get_v1)
    await cache.check_and_update()
    assert cache.version == 1
    assert len(cache.rules) == 1

    # 2-holat: Veb-saytdan yangi qoida qo'shildi, versiya 2 ga o'zgardi
    async def mock_get_v2(self, url, headers=None, timeout=None):
        if "version" in str(url):
            return httpx.Response(200, json={"version": 2})
        return httpx.Response(
            200,
            json={
                "version": 2,
                "rules": [
                    {"id": 1, "keyword": "suv yo'q", "priority": 50},
                    {"id": 2, "keyword": "quvur teshildi", "priority": 70},
                ],
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get_v2)
    await cache.check_and_update()
    assert cache.version == 2
    assert len(cache.rules) == 2


@pytest.mark.asyncio
async def test_rules_cache_backend_down_fallback(monkeypatch):
    cache = RulesCache(
        backend_url="http://testbackend",
        api_key="bot_secret_key",
        refresh_interval=1,
    )

    # Dastlab kesh to'ldiriladi
    cache._rules = [{"id": 1, "keyword": "suv yo'q"}]
    cache._version = 5
    cache._rules_loaded = True

    # Keyin backend uzilib qoladi
    async def mock_get_error(self, url, headers=None, timeout=None):
        raise httpx.NetworkError("Backend aloqasi uzildi")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get_error)

    success = await cache.fetch_rules()
    assert success is False
    # Kesh yo'qolib ketmasligi kerak!
    assert len(cache.rules) == 1
    assert cache.rules[0]["keyword"] == "suv yo'q"
    assert cache.is_stale is True
