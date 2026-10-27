from datetime import UTC, datetime, timedelta

from tests.conftest import BOT, add_rule, make_message


def test_stats_empty_state(auth):
    s = auth.get("/api/v1/dashboard/stats").json()
    assert s["cards"]["total_incidents"] == 0 and s["cards"]["messages_today"] == 0
    assert s["bot"]["status"] == "UNKNOWN" and s["last_sync_at"] is None


def test_stats_counts_are_correct(auth, source):
    add_rule(auth)
    add_rule(auth, "suv yo'q", category="SUPPLY_OUTAGE")
    add_rule(auth, "bosim yo'q", category="LOW_PRESSURE")
    auth.headers.update(BOT)
    ids = []
    for i, t in enumerate(["quvur yorildi A", "suv yo'q B", "bosim yo'q C"]):
        ids.append(auth.post("/api/v1/bot/messages", json=make_message(i, t)).json()["incident_id"])
    auth.post("/api/v1/bot/messages", json=make_message(50, "quvur yorildi, hozir tuzatildi"))
    auth.post("/api/v1/bot/messages", json=make_message(51, "oddiy xabar"))
    del auth.headers["X-Bot-Api-Key"]
    auth.patch(f"/api/v1/incidents/{ids[0]}", json={"status": "RESOLVED"})
    auth.patch(f"/api/v1/incidents/{ids[1]}", json={"status": "IN_PROGRESS"})

    s = auth.get("/api/v1/dashboard/stats").json()
    c = s["cards"]
    assert c["total_incidents"] == 3
    assert (c["open_incidents"], c["in_progress_incidents"], c["resolved_incidents"]) == (1, 1, 1)
    assert c["messages_today"] == 5
    assert c["unreviewed_incidents"] == 1  # faqat ids[2]: tarix ham, izoh ham yo'q
    assert c["review_required_messages"] == 1
    assert s["by_status"]["RESOLVED"] == 1 and s["by_category"]["LOW_PRESSURE"] == 1
    assert s["sources"][0]["messages_24h"] == 5
    assert s["last_sync_at"] is not None


def test_today_window_excludes_yesterday(auth, source, db):
    from app.models import SourceMessage
    from app.models.enums import ProcessingStatus

    db.add(SourceMessage(
        source_id=source.id, telegram_message_id=1, message_text="eski",
        telegram_timestamp=datetime.now(UTC), received_at=datetime.now(UTC) - timedelta(days=2),
        processing_status=ProcessingStatus.NO_MATCH, matched_rule_ids=[]))
    db.commit()
    assert auth.get("/api/v1/dashboard/stats").json()["cards"]["messages_today"] == 0


def test_bot_status_follows_heartbeat(auth):
    assert auth.get("/api/v1/system/bot-status").json()["status"] == "UNKNOWN"
    hb = auth.post("/api/v1/bot/heartbeat", json={"rules_loaded": False}, headers=BOT)
    assert hb.status_code == 200
    assert auth.get("/api/v1/system/bot-status").json()["status"] == "DEGRADED"
    auth.post("/api/v1/bot/heartbeat", json={"rules_loaded": True, "rules_version": 3}, headers=BOT)
    st = auth.get("/api/v1/system/bot-status").json()
    assert st["status"] == "ONLINE" and st["rules_version"] == 3


def test_bot_offline_when_heartbeat_stale(auth, db):
    from app.services import settings_service as ss

    old = (datetime.now(UTC) - timedelta(minutes=10)).isoformat()
    ss.set_setting(db, ss.BOT_HEARTBEAT, {"at": old, "rules_loaded": True})
    db.commit()
    assert auth.get("/api/v1/system/bot-status").json()["status"] == "OFFLINE"


def test_recent_lists(auth, source):
    add_rule(auth)
    auth.post("/api/v1/bot/messages", json=make_message(1, "quvur yorildi"), headers=BOT)
    assert len(auth.get("/api/v1/dashboard/recent-incidents").json()) == 1
    m = auth.get("/api/v1/dashboard/recent-messages").json()
    assert m[0]["source_name"] == "Test kanal" and m[0]["processing_status"] == "INCIDENT_CREATED"


def test_health_is_public_and_leaks_nothing(client):
    r = client.get("/api/v1/system/health")
    assert r.status_code == 200 and r.json() == {"status": "ok", "database": "up"}


def test_source_crud(auth):
    body = {"name": "Kanal A", "telegram_chat_id": -100123, "telegram_username": "@kanal_a",
            "source_type": "CHANNEL"}
    r = auth.post("/api/v1/sources", json=body)
    assert r.status_code == 201 and r.json()["telegram_username"] == "kanal_a"
    sid = r.json()["id"]
    assert auth.post("/api/v1/sources", json=body).status_code == 409
    r = auth.patch(f"/api/v1/sources/{sid}", json={"name": "Kanal B", "is_active": False})
    assert r.json()["name"] == "Kanal B" and r.json()["is_active"] is False
    assert auth.get("/api/v1/sources?is_active=false").json()["total"] == 1
    assert auth.get("/api/v1/sources?q=kanal").json()["total"] == 1
    assert auth.get("/api/v1/sources/999").status_code == 404
    bad = auth.post("/api/v1/sources", json={**body, "telegram_chat_id": 5, "telegram_username": "a b"})
    assert bad.status_code == 422

    # Resolve testi (username yoki havola orqali)
    res_resp = auth.post("/api/v1/sources/resolve", json={"identifier": "https://t.me/suv_kanali"})
    assert res_resp.status_code == 200
    res_data = res_resp.json()
    assert res_data["telegram_username"] == "suv_kanali"
    assert res_data["telegram_chat_id"] < 0

    # Chat_id siz faqat username orqali manba qo'shish
    auto_resp = auth.post("/api/v1/sources", json={"telegram_username": "https://t.me/yangi_kanal_2026"})
    assert auto_resp.status_code == 201
    assert auto_resp.json()["telegram_username"] == "yangi_kanal_2026"
    assert auto_resp.json()["telegram_chat_id"] < 0



def test_unexpected_error_does_not_leak_details(app, user, monkeypatch):
    from fastapi.testclient import TestClient

    from app.services import dashboard_service

    def boom(db):  # noqa: ANN001
        raise RuntimeError("secret-db-password-xyz")

    monkeypatch.setattr(dashboard_service, "get_stats", boom)
    c = TestClient(app, raise_server_exceptions=False)
    c.post("/api/v1/auth/login", json={"identifier": "ali", "password": "Sinov-parol-12345"})
    r = c.get("/api/v1/dashboard/stats")
    assert r.status_code == 500
    assert "secret-db-password" not in r.text and "Traceback" not in r.text
    assert r.json()["error"]["code"] == "internal_error"


def test_bot_register_source(client, auth):
    payload = {
        "chat_id": -1001234567890,
        "chat_title": "Yunusobod Aholi Guruhi",
        "chat_username": "yunusobod_suv",
        "source_type": "GROUP",
    }
    # Unauthenticated rejected
    assert client.post("/api/v1/bot/register-source", json=payload).status_code == 401

    # Authenticated bot registers source
    r = client.post("/api/v1/bot/register-source", json=payload, headers=BOT)
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["created"] is True
    source_id = data["source_id"]

    # Verify source appears in web sources list
    sources_res = auth.get("/api/v1/sources").json()
    assert any(s["id"] == source_id for s in sources_res["items"])

    # Registering again activates/updates without error
    r2 = client.post("/api/v1/bot/register-source", json=payload, headers=BOT)
    assert r2.status_code == 200
    assert r2.json()["created"] is False


def test_delete_source(auth):
    # Create source
    r = auth.post(
        "/api/v1/sources",
        json={"name": "O'chirish kanali", "telegram_username": "del_channel", "telegram_chat_id": 999111, "source_type": "CHANNEL"},
    )
    assert r.status_code == 201
    source_id = r.json()["id"]

    # Delete source
    del_r = auth.delete(f"/api/v1/sources/{source_id}")
    assert del_r.status_code == 204

    # Verify not in list
    sources_res = auth.get("/api/v1/sources").json()
    assert not any(s["id"] == source_id for s in sources_res["items"])


