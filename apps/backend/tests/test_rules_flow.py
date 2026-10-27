"""Majburiy oqim (backend tomoni): qoida -> faol ro'yxat -> xabar -> hodisa -> deaktivatsiya.

Eslatma: bu test SQLite xotirasida ishlaydi; PostgreSQL bilan emas. Botning o'zi
(qoidalarni qayta ishga tushirmasdan olishi) bot qismi yozilganda alohida tekshiriladi.
"""
from tests.conftest import BOT, add_rule, make_message


def test_full_dynamic_rule_flow(auth, source):
    msg = lambda i: auth.post(  # noqa: E731
        "/api/v1/bot/messages", json=make_message(i, "Mahallada quvur yorildi"), headers=BOT
    ).json()

    # Qoida yo'q: xabar hodisa yaratmaydi
    assert msg(1)["status"] == "NO_MATCH"

    # 1-3. Sayt orqali qoida qo'shiladi; faol qoidalar endpointi uni qaytaradi
    rule = add_rule(auth, "quvur yorildi")
    active = auth.get("/api/v1/detection-rules/active", headers=BOT).json()
    assert [r["id"] for r in active["rules"]] == [rule["id"]]
    version_before = active["version"]

    # 5. Mos xabar hodisa yaratadi
    created = msg(2)
    assert created["status"] == "INCIDENT_CREATED"

    # 7. Takroriy xabar ikkinchi hodisa yaratmaydi
    assert msg(2)["duplicate"] is True
    assert auth.get("/api/v1/incidents").json()["total"] == 1

    # 6. Deaktivatsiya: versiya o'zgaradi, yangi xabar hodisa yaratmaydi
    auth.patch(f"/api/v1/detection-rules/{rule['id']}", json={"is_active": False})
    after = auth.get("/api/v1/detection-rules/active", headers=BOT).json()
    assert after["rules"] == [] and after["version"] > version_before
    assert msg(3)["status"] == "NO_MATCH"
    assert auth.get("/api/v1/incidents").json()["total"] == 1
