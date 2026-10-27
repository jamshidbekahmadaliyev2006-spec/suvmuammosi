from tests.conftest import BOT, add_rule


def test_create_and_read_rule(auth):
    rule = add_rule(auth, "quvur yorildi")
    r = auth.get(f"/api/v1/detection-rules/{rule['id']}")
    assert r.status_code == 200
    assert r.json()["created_by_username"] == "ali"
    assert r.json()["is_active"] is True


def test_duplicate_after_normalization_rejected(auth):
    add_rule(auth, "suv o'chdi")
    r = auth.post("/api/v1/detection-rules", json={
        "name": "x", "keyword": "SUV  O‘CHDI", "category": "SUPPLY_OUTAGE"})
    assert r.status_code == 409


def test_edit_rule_and_version_bumps(auth):
    rule = add_rule(auth)
    v1 = auth.get("/api/v1/detection-rules/version").json()["version"]
    r = auth.patch(f"/api/v1/detection-rules/{rule['id']}", json={"priority": 10, "name": "Yangi"})
    assert r.status_code == 200 and r.json()["priority"] == 10
    assert auth.get("/api/v1/detection-rules/version").json()["version"] == v1 + 1


def test_deactivate_and_activate(auth):
    rule = add_rule(auth)
    url = f"/api/v1/detection-rules/{rule['id']}"
    assert auth.patch(url, json={"is_active": False}).json()["is_active"] is False
    assert auth.get("/api/v1/detection-rules/active").json()["rules"] == []
    assert auth.patch(url, json={"is_active": True}).json()["is_active"] is True
    assert len(auth.get("/api/v1/detection-rules/active").json()["rules"]) == 1


def test_active_endpoint_works_with_bot_key(client, auth):
    add_rule(auth)
    bot = client.__class__(client.app)
    r = bot.get("/api/v1/detection-rules/active", headers=BOT)
    assert r.status_code == 200 and r.json()["rules"][0]["keyword"] == "quvur yorildi"


def test_active_endpoint_rejects_wrong_bot_key_and_anonymous(client):
    assert client.get("/api/v1/detection-rules/active").status_code == 401
    r = client.get("/api/v1/detection-rules/active", headers={"X-Bot-Api-Key": "x"})
    assert r.status_code == 401


def test_invalid_rule_data_rejected(auth):
    base = {"name": "a", "keyword": "ok kalit", "category": "LEAK"}
    for bad in [
        {**base, "keyword": "a"},
        {**base, "keyword": "   "},
        {**base, "category": "NOMA'LUM"},
        {**base, "match_type": "REGEX"},
        {**base, "priority": 0},
        {**base, "priority": 101},
        {**base, "name": ""},
    ]:
        r = auth.post("/api/v1/detection-rules", json=bad)
        assert r.status_code == 422, bad
        assert r.json()["error"]["code"] == "validation_error"


def test_unknown_rule_404(auth):
    assert auth.get("/api/v1/detection-rules/9999").status_code == 404
    assert auth.patch("/api/v1/detection-rules/9999", json={"priority": 5}).status_code == 404


def test_list_filters_and_pagination(auth):
    add_rule(auth, "quvur yorildi")
    add_rule(auth, "suv yo'q", category="SUPPLY_OUTAGE")
    add_rule(auth, "bosim yo'q", category="LOW_PRESSURE")
    assert auth.get("/api/v1/detection-rules?category=LOW_PRESSURE").json()["total"] == 1
    assert auth.get("/api/v1/detection-rules?q=suv").json()["total"] == 1
    page = auth.get("/api/v1/detection-rules?page=2&page_size=2").json()
    assert page["total"] == 3 and len(page["items"]) == 1


def test_rule_changes_are_audited(auth, db):
    from app.models import AuditLog

    rule = add_rule(auth)
    auth.patch(f"/api/v1/detection-rules/{rule['id']}", json={"is_active": False})
    actions = [a.action for a in db.query(AuditLog)]
    assert "rule.create" in actions and "rule.deactivate" in actions


def test_delete_rule(auth):
    rule = add_rule(auth, "quvur yorildi o'chirish")
    r = auth.delete(f"/api/v1/detection-rules/{rule['id']}")
    assert r.status_code == 204
    assert auth.get(f"/api/v1/detection-rules/{rule['id']}").status_code == 404

