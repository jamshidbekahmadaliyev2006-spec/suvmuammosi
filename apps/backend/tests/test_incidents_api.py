from datetime import UTC, datetime, timedelta

from tests.conftest import BOT, add_rule, make_message


def seed(auth, n=3):
    add_rule(auth)
    add_rule(auth, "suv yo'q", category="SUPPLY_OUTAGE", priority=60)
    ids = []
    for i in range(n):
        text = ("quvur yorildi" if i % 2 == 0 else "suv yo'q") + f" manzil{i} " + "x" * i * 10
        ts = (datetime.now(UTC) + timedelta(seconds=i * 5)).isoformat()
        r = auth.post("/api/v1/bot/messages", json=make_message(100 + i, text, timestamp=ts), headers=BOT)
        ids.append(r.json()["incident_id"])
    return ids


def test_unknown_incident_404(auth):
    assert auth.get("/api/v1/incidents/999").status_code == 404
    assert auth.patch("/api/v1/incidents/999", json={"status": "RESOLVED"}).status_code == 404
    assert auth.get("/api/v1/incidents/999/history").status_code == 404
    assert auth.post("/api/v1/incidents/999/comments", json={"comment": "a"}).status_code == 404


def test_status_change_saves_history_and_audit(auth, source, db):
    from app.models import AuditLog

    (iid,) = seed(auth, 1)
    r = auth.patch(f"/api/v1/incidents/{iid}", json={"status": "IN_PROGRESS", "comment": "Brigada yo'lda"})
    assert r.status_code == 200 and r.json()["status"] == "IN_PROGRESS"
    r = auth.patch(f"/api/v1/incidents/{iid}",
                   json={"status": "RESOLVED", "resolution_notes": "Quvur almashtirildi"})
    assert r.json()["resolved_at"] is not None
    hist = auth.get(f"/api/v1/incidents/{iid}/history").json()
    assert [h["new_status"] for h in hist] == ["RESOLVED", "IN_PROGRESS"]
    assert hist[1]["old_status"] == "OPEN" and hist[1]["changed_by_username"] == "ali"
    assert hist[1]["comment"] == "Brigada yo'lda"
    assert db.query(AuditLog).filter_by(action="incident.status_change").count() == 2


def test_reopening_clears_resolved_at(auth, source):
    (iid,) = seed(auth, 1)
    auth.patch(f"/api/v1/incidents/{iid}", json={"status": "RESOLVED"})
    r = auth.patch(f"/api/v1/incidents/{iid}", json={"status": "OPEN"})
    assert r.json()["resolved_at"] is None


def test_invalid_status_rejected(auth, source):
    (iid,) = seed(auth, 1)
    assert auth.patch(f"/api/v1/incidents/{iid}", json={"status": "DELETED"}).status_code == 422


def test_no_delete_endpoint(auth, source):
    (iid,) = seed(auth, 1)
    assert auth.delete(f"/api/v1/incidents/{iid}").status_code == 405


def test_comments(auth, source):
    (iid,) = seed(auth, 1)
    r = auth.post(f"/api/v1/incidents/{iid}/comments", json={"comment": "Tekshirildi"})
    assert r.status_code == 201 and r.json()["username"] == "ali"
    assert auth.post(f"/api/v1/incidents/{iid}/comments", json={"comment": "  "}).status_code == 422
    assert len(auth.get(f"/api/v1/incidents/{iid}").json()["comments"]) == 1


def test_filters_search_sort_pagination(auth, source):
    ids = seed(auth, 5)
    auth.patch(f"/api/v1/incidents/{ids[0]}", json={"status": "RESOLVED"})
    g = lambda qs: auth.get("/api/v1/incidents" + qs).json()  # noqa: E731
    assert g("")["total"] == 5
    assert g("?status=RESOLVED")["total"] == 1
    assert g("?category=SUPPLY_OUTAGE")["total"] == 2
    assert g("?q=manzil3")["total"] == 1
    assert g(f"?source_id={source.id}")["total"] == 5
    assert g("?source_id=9999")["total"] == 0
    page = g("?page=2&page_size=2")
    assert page["total"] == 5 and len(page["items"]) == 2
    asc = [i["id"] for i in g("?sort_by=first_seen_at&order=asc")["items"]]
    assert asc == sorted(asc)
    pr = [i["priority"] for i in g("?sort_by=priority&order=desc")["items"]]
    assert pr[0] == "HIGH" and pr[-1] == "MEDIUM"
    assert g("?date_from=2000-01-01&date_to=2000-01-02")["total"] == 0
    assert g("?date_from=2000-01-01")["total"] == 5


def test_search_treats_wildcards_literally(auth, source):
    seed(auth, 2)
    assert auth.get("/api/v1/incidents?q=%25").json()["total"] == 0
    assert auth.get("/api/v1/incidents?q=_").json()["total"] == 0


def test_bad_pagination_and_sort_rejected(auth):
    assert auth.get("/api/v1/incidents?page=0").status_code == 422
    assert auth.get("/api/v1/incidents?page_size=1000").status_code == 422
    assert auth.get("/api/v1/incidents?sort_by=password").status_code == 422
