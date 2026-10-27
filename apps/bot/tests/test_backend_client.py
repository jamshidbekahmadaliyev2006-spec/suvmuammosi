import httpx
import pytest

from services.backend_client import BackendClient


@pytest.mark.asyncio
async def test_backend_client_send_message_success(monkeypatch):
    client = BackendClient(backend_url="http://testbackend", api_key="test_key", max_retries=2)

    payload = {"chat_id": 123, "message_id": 456, "text": "suv yo'q", "timestamp": "2026-10-23T12:00:00"}
    expected_response = {"status": "INCIDENT_CREATED", "incident_id": 77, "duplicate": False}

    async def mock_post(self, url, json=None, headers=None):
        assert headers.get("x-bot-api-key") == "test_key"
        return httpx.Response(201, json=expected_response)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    resp = await client.send_message(payload)
    assert resp == expected_response


@pytest.mark.asyncio
async def test_backend_client_retry_and_eventual_success(monkeypatch):
    client = BackendClient(backend_url="http://testbackend", api_key="test_key", max_retries=3)

    attempts = 0

    async def mock_post(self, url, json=None, headers=None):
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise httpx.NetworkError("Vaqtinchalik tarmoq xatosi")
        return httpx.Response(200, json={"status": "OK", "attempt": attempts})

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    resp = await client.send_message({"chat_id": 1, "message_id": 2, "text": "test"})
    assert resp == {"status": "OK", "attempt": 2}
    assert attempts == 2


@pytest.mark.asyncio
async def test_backend_client_heartbeat_success(monkeypatch):
    client = BackendClient(backend_url="http://testbackend", api_key="test_key")

    async def mock_post(self, url, json=None, headers=None):
        assert json.get("rules_loaded") is True
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    ok = await client.send_heartbeat(
        bot_version="0.1.0",
        rules_version=10,
        rules_loaded=True,
    )
    assert ok is True


@pytest.mark.asyncio
async def test_backend_client_cancel_incident(monkeypatch):
    client = BackendClient(backend_url="http://testbackend", api_key="test_key")

    async def mock_post(self, url, json=None, headers=None):
        assert json.get("incident_id") == 42
        assert json.get("chat_id") == 999
        return httpx.Response(200, json={"ok": True, "cancelled": True})

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    ok = await client.cancel_incident(42, 999)
    assert ok is True

