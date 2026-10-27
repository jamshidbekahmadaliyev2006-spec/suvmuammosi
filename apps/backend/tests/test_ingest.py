from tests.conftest import BOT, add_rule, make_message


def post(client, **kw):
    return client.post("/api/v1/bot/messages", json=make_message(**kw), headers=BOT)


def test_unauthorized_bot_request_rejected(client, source):
    r = client.post("/api/v1/bot/messages", json=make_message(1, "quvur yorildi"))
    assert r.status_code == 401
    r = client.post("/api/v1/bot/messages", json=make_message(1, "x"), headers={"X-Bot-Api-Key": "x"})
    assert r.status_code == 401
    assert client.post("/api/v1/bot/heartbeat", json={}).status_code == 401


def test_matching_message_creates_incident(auth, source):
    add_rule(auth)
    r = post(auth, message_id=1, text="Chilonzorda quvur yorildi")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "INCIDENT_CREATED" and body["incident_id"] and not body["duplicate"]
    inc = auth.get(f"/api/v1/incidents/{body['incident_id']}").json()
    assert inc["status"] == "OPEN" and inc["category"] == "PIPE_BURST" and inc["priority"] == "HIGH"
    assert inc["district"] == "Toshkent sh., Chilonzor tumani" and (inc["address"] is None or inc["address"] == "Chilonzor")
    assert inc["first_message"]["message_text"] == "Chilonzorda quvur yorildi"


def test_duplicate_message_is_idempotent(auth, source):
    add_rule(auth)
    first = post(auth, message_id=7, text="quvur yorildi").json()
    second = post(auth, message_id=7, text="quvur yorildi").json()
    assert second["duplicate"] is True and second["incident_id"] == first["incident_id"]
    assert auth.get("/api/v1/incidents").json()["total"] == 1


def test_no_match_creates_no_incident(auth, source):
    add_rule(auth)
    assert post(auth, message_id=1, text="Bugun yig'ilish bo'ladi").json()["status"] == "NO_MATCH"
    assert auth.get("/api/v1/incidents").json()["total"] == 0


def test_unregistered_or_inactive_source_rejected(auth, source):
    assert post(auth, message_id=1, text="x", chat_id=-999).status_code == 404
    auth.patch(f"/api/v1/sources/{source.id}", json={"is_active": False})
    assert post(auth, message_id=2, text="quvur yorildi").status_code == 404


def test_negation_goes_to_review_without_incident(auth, source):
    add_rule(auth, "suv ta'minoti muammosi", category="SUPPLY_OUTAGE")
    r = post(auth, message_id=1, text="Suv ta'minoti muammosi yo'q").json()
    assert r["status"] == "REVIEW_REQUIRED" and r["incident_id"] is None
    assert auth.get("/api/v1/incidents").json()["total"] == 0


def test_planned_repair_category(auth, source):
    add_rule(auth, "quvur ta'mirlash", category="PIPE_BURST")
    r = post(auth, message_id=1, text="Ertaga quvur ta'mirlash ishlari bo'ladi").json()
    inc = auth.get(f"/api/v1/incidents/{r['incident_id']}").json()
    assert inc["category"] == "PLANNED_REPAIR"


def test_similar_messages_link_to_same_incident(auth, source):
    add_rule(auth)
    a = post(auth, message_id=1, text="Chilonzor 5-kvartal quvur yorildi").json()
    b = post(auth, message_id=2, text="Chilonzor 5-kvartal quvur yorildi, shoshiling").json()
    assert b["status"] == "LINKED" and b["incident_id"] == a["incident_id"]
    msgs = auth.get(f"/api/v1/incidents/{a['incident_id']}/messages").json()
    assert len(msgs) == 2


def test_different_text_makes_separate_incident(auth, source):
    add_rule(auth)
    a = post(auth, message_id=1, text="Chilonzor 5-kvartal quvur yorildi").json()
    b = post(auth, message_id=2, text="Yunusobod ko'chasida quvur yorildi, ko'p suv").json()
    assert a["incident_id"] != b["incident_id"]


def test_same_message_id_in_other_source_is_not_duplicate(auth, db, source):
    from app.models import MonitoringSource
    from app.models.enums import SourceType

    db.add(MonitoringSource(name="Ikkinchi", telegram_chat_id=-2002, source_type=SourceType.GROUP))
    db.commit()
    add_rule(auth)
    post(auth, message_id=1, text="quvur yorildi")
    r = post(auth, message_id=1, text="quvur yorildi", chat_id=-2002).json()
    assert r["duplicate"] is False


def test_source_last_message_updated(auth, source):
    add_rule(auth)
    post(auth, message_id=1, text="quvur yorildi")
    s = auth.get(f"/api/v1/sources/{source.id}").json()
    assert s["last_message_at"] and s["last_received_at"]


def test_gps_location_message_extracts_district_and_address(auth, source):
    add_rule(auth)
    text = "GPS Lokatsiya: https://maps.google.com/?q=41.365,69.285 quvur yorildi"
    r = post(auth, message_id=99, text=text)
    assert r.status_code == 200
    data = r.json()
    assert data["incident_id"] is not None
    inc = auth.get(f"/api/v1/incidents/{data['incident_id']}").json()
    assert inc["district"] is not None
    assert "Yunusobod" in inc["district"]
    assert inc["address"] is not None


def test_russian_and_english_message_ingest(auth, source):
    # Ruscha qoida
    auth.post(
        "/api/v1/detection-rules",
        json={"name": "Прорыв трубы", "keyword": "прорыв трубы", "category": "PIPE_BURST", "priority": 85},
    )
    # Inglizcha qoida
    auth.post(
        "/api/v1/detection-rules",
        json={"name": "Water leak", "keyword": "water leak", "category": "LEAK", "priority": 60},
    )

    # Ruscha xabar (morfologik variant: "прорвало трубу" va "Юнусабад")
    r1 = post(auth, message_id=101, text="В Юнусабаде прорвало трубу, вода хлещет!")
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["status"] == "INCIDENT_CREATED"
    assert d1["incident_id"] is not None
    inc1 = auth.get(f"/api/v1/incidents/{d1['incident_id']}").json()
    assert inc1["category"] == "PIPE_BURST"
    assert "Yunusobod" in inc1["district"]

    # Inglizcha xabar
    r2 = post(auth, message_id=102, text="Water leak detected on the street")
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["status"] == "INCIDENT_CREATED"
    assert d2["incident_id"] is not None
    inc2 = auth.get(f"/api/v1/incidents/{d2['incident_id']}").json()
    assert inc2["category"] == "LEAK"


