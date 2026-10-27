"""16-bosqichli to'liq End-to-End integratsiya testi.

Spetsifikatsiyadagi barcha 16 ta amaliy talabni to'liq qamrab oladi:
1. Tizim muhitini tayyorlash.
2. Foydalanuvchi yaratish va DB migratsiyasi.
3. Login va CSRF token olish.
4. Sayt orqali yangi faol qoida yaratish.
5. Qoidaning bazada saqlanishi.
6. Backend faol qoidalar endpointidan qaytishi.
7. Bot qoidalar keshi yangi qoidani restartsiz olishi.
8. Telegram xabarini yuborish.
9. Hodisa yaratilishi va dashboardda ko'rinishi.
10. Xuddi shu xabarni takror yuborish.
11. Takroriy xabar yangi hodisa yaratmasligi (idempotentlik).
12. Qoidani nofaol (is_active=False) qilish.
13. Bot yangi versiyani olishi.
14. Yangi xabar nofaol qoida bo'yicha hodisa yaratmasligi.
15. Hodisa statusini o'zgartirish va tarix yozilishi.
16. Logout va himoyalangan endpoint rad etilishi.
"""
from datetime import UTC, datetime

from starlette.testclient import TestClient

from app.core.security import hash_password
from app.models import Incident, IncidentStatusHistory, MonitoringSource, User
from app.models.enums import IncidentStatus, SourceType


def test_16_step_complete_e2e_flow(client: TestClient, db):
    bot_headers = {"x-bot-api-key": "test-bot-key-0123456789abcdef"}

    # 1-2. Test manba va foydalanuvchisini bazaga kiritish
    src = MonitoringSource(
        name="Toshkent Suv Kanali",
        telegram_chat_id=-100998877,
        source_type=SourceType.CHANNEL,
        is_active=True,
    )
    db.add(src)

    user = User(
        username="suvchi_ali",
        email="ali@suvnazorat.uz",
        password_hash=hash_password("SuperParol12345!"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(src)
    db.refresh(user)

    # 3. Foydalanuvchi tizimga login qiladi
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "suvchi_ali", "password": "SuperParol12345!"},
    )
    assert login_resp.status_code == 200, f"Login xatosi: {login_resp.text}"
    csrf_token = login_resp.json()["csrf_token"]
    auth_headers = {"X-CSRF-Token": csrf_token}

    # 4. Sayt orqali "quvur yorildi" nomli yangi qoida yaratish
    rule_payload = {
        "name": "Quvur yorilishi signali",
        "keyword": "quvur yorildi",
        "category": "PIPE_BURST",
        "match_type": "PHRASE",
        "priority": 85,
        "is_active": True,
    }
    create_rule_resp = client.post(
        "/api/v1/detection-rules",
        json=rule_payload,
        headers=auth_headers,
    )
    assert create_rule_resp.status_code == 201
    rule_data = create_rule_resp.json()
    rule_id = rule_data["id"]

    # 5. Qoidaning bazada saqlanganini tekshirish
    rule_in_db = client.get(f"/api/v1/detection-rules/{rule_id}", headers=auth_headers).json()
    assert rule_in_db["name"] == "Quvur yorilishi signali"
    assert rule_in_db["keyword"] == "quvur yorildi"
    assert rule_in_db["is_active"] is True

    # 6. Backendning faol qoidalar endpointidan shu qoida qaytishini tekshirish
    active_rules_resp = client.get("/api/v1/detection-rules/active", headers=bot_headers).json()
    assert active_rules_resp["version"] >= 1
    active_keywords = [r["keyword"] for r in active_rules_resp["rules"]]
    assert "quvur yorildi" in active_keywords

    # 7. Bot keshi (simulyatsiya): Faol qoidalar keshga yuklanadi
    bot_cached_rules = active_rules_resp["rules"]
    assert any(r["id"] == rule_id for r in bot_cached_rules)

    # 8. Test Telegram xabarini yuborish
    msg_timestamp = datetime.now(UTC).isoformat()
    msg_payload = {
        "chat_id": src.telegram_chat_id,
        "message_id": 5001,
        "chat_title": src.name,
        "text": "Shoshilinch! Ko'chamizda katta quvur yorildi, suv toshmoqda!",
        "timestamp": msg_timestamp,
    }
    ingest_resp = client.post("/api/v1/bot/messages", json=msg_payload, headers=bot_headers)
    assert ingest_resp.status_code == 200
    ingest_data = ingest_resp.json()
    incident_id = ingest_data["incident_id"]
    assert incident_id is not None
    assert ingest_data["duplicate"] is False
    assert rule_id in ingest_data["matched_rule_ids"]

    # 9. Hodisaning yaratilgani va dashboardda ko'rinishini tekshirish
    stats_resp = client.get("/api/v1/dashboard/stats", headers=auth_headers).json()
    assert stats_resp["cards"]["total_incidents"] >= 1
    assert stats_resp["cards"]["open_incidents"] >= 1

    recent_incidents = client.get("/api/v1/dashboard/recent-incidents", headers=auth_headers).json()
    recent_ids = [inc["id"] for inc in recent_incidents]
    assert incident_id in recent_ids

    # 10. Xuddi shu Telegram xabarini ikkinchi marta takroran yuborish
    ingest_dup_resp = client.post("/api/v1/bot/messages", json=msg_payload, headers=bot_headers)
    assert ingest_dup_resp.status_code == 200
    dup_data = ingest_dup_resp.json()

    # 11. Ikkinchi hodisa yaratilmaganini tekshirish (idempotentlik)
    assert dup_data["duplicate"] is True
    assert dup_data["incident_id"] == incident_id
    total_after_dup = db.query(Incident).count()
    assert total_after_dup == 1

    # 12. Saytdan qoidani nofaol (is_active=False) qilish
    patch_rule_resp = client.patch(
        f"/api/v1/detection-rules/{rule_id}",
        json={"is_active": False},
        headers=auth_headers,
    )
    assert patch_rule_resp.status_code == 200
    assert patch_rule_resp.json()["is_active"] is False

    # 13. Bot yangi qoidalar versiyasini olganini tekshirish
    active_after_deact = client.get("/api/v1/detection-rules/active", headers=bot_headers).json()
    active_ids_after = [r["id"] for r in active_after_deact["rules"]]
    assert rule_id not in active_ids_after

    # 14. Yangi xabar nofaol qoida bo'yicha yangi hodisa yaratmasligini tekshirish
    new_msg_payload = {
        "chat_id": src.telegram_chat_id,
        "message_id": 5002,
        "chat_title": src.name,
        "text": "Boshqa joyda ham quvur yorildi degan xabar keldi",
        "timestamp": datetime.now(UTC).isoformat(),
    }
    ingest_no_match = client.post("/api/v1/bot/messages", json=new_msg_payload, headers=bot_headers).json()
    assert ingest_no_match["incident_id"] is None
    assert ingest_no_match["status"] == "NO_MATCH"
    assert db.query(Incident).count() == 1  # Yangi hodisa yaratilmadi!

    # 15. Hodisa statusini o'zgartirish va tarix yozilganini tekshirish
    change_status_resp = client.patch(
        f"/api/v1/incidents/{incident_id}",
        json={
            "status": "RESOLVED",
            "comment": "Ta'mirlash brigadasi ishni yakunladi",
            "resolution_notes": "Quvur payvandlandi va suv ta'minoti tiklandi",
        },
        headers=auth_headers,
    )
    assert change_status_resp.status_code == 200
    assert change_status_resp.json()["status"] == "RESOLVED"
    assert change_status_resp.json()["resolution_notes"] is not None

    hist_entries = db.query(IncidentStatusHistory).filter_by(incident_id=incident_id).all()
    assert len(hist_entries) >= 1
    assert any(h.new_status == IncidentStatus.RESOLVED for h in hist_entries)

    # 16. Logout qilish va himoyalangan API so'rovi rad etilishini tekshirish
    logout_resp = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert logout_resp.status_code == 200

    # Sessiyasiz himoyalangan endpointga murojaat qilish
    unauth_resp = client.get("/api/v1/incidents")
    assert unauth_resp.status_code in (401, 403)
