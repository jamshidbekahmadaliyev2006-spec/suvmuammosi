from app.models import AuditLog, User
from tests.conftest import PASSWORD


def login(client, identifier="ali", password=PASSWORD):
    return client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})


def test_login_success_sets_httponly_cookie(client, user):
    r = login(client)
    assert r.status_code == 200
    assert r.json()["user"]["role"] == "USER"
    assert "httponly" in r.headers["set-cookie"].lower()
    assert "password" not in r.text


def test_login_by_email(client, user):
    assert login(client, "ALI@example.uz").status_code == 200


def test_wrong_password_rejected_with_generic_message(client, user):
    r = login(client, password="xato")
    r2 = login(client, identifier="yoq-odam")
    assert r.status_code == r2.status_code == 401
    assert r.json() == r2.json()  # hisob mavjudligi oshkor bo'lmaydi


def test_protected_endpoint_requires_auth(client):
    for path in ["/api/v1/auth/me", "/api/v1/dashboard/stats", "/api/v1/incidents",
                 "/api/v1/detection-rules", "/api/v1/sources"]:
        assert client.get(path).status_code == 401


def test_inactive_user_cannot_login(client, db, user):
    db.get(User, user.id).is_active = False
    db.commit()
    assert login(client).status_code == 401


def test_inactive_user_session_stops_working(auth, db, user):
    assert auth.get("/api/v1/auth/me").status_code == 200
    db.get(User, user.id).is_active = False
    db.commit()
    assert auth.get("/api/v1/auth/me").status_code == 401


def test_logout_really_revokes_session(auth):
    token = auth.cookies.get("sn_session")
    assert auth.post("/api/v1/auth/logout").status_code == 200
    # Eski cookie qayta yuborilsa ham sessiya yaroqsiz
    auth.cookies.set("sn_session", token)
    assert auth.get("/api/v1/auth/me").status_code == 401


def test_csrf_required_for_unsafe_methods(auth):
    del auth.headers["X-CSRF-Token"]
    r = auth.post("/api/v1/auth/logout")
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "csrf_failed"


def test_login_rate_limited(client, user):
    for _ in range(5):
        assert login(client, password="xato").status_code == 401
    r = login(client, password="xato")
    assert r.status_code == 429
    assert "retry-after" in r.headers
    assert login(client).status_code == 429  # to'g'ri parol ham vaqtincha bloklanadi


def test_login_and_logout_are_audited(auth, db):
    auth.post("/api/v1/auth/logout")
    actions = {a.action for a in db.query(AuditLog)}
    assert {"auth.login", "auth.logout"} <= actions


def test_password_is_hashed(db, user):
    assert user.password_hash.startswith("$argon2")
    assert PASSWORD not in user.password_hash
