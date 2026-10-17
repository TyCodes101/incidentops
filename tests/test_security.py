from datetime import timedelta

from sqlalchemy import select

from incidentops.db import get_db
from incidentops.main import app
from incidentops.models import LoginSession, utcnow


def account(client, headers, role):
    result = client.post(
        "/users",
        headers=headers,
        json={"username": role, "password": "safe-test-password", "role": role},
    )
    assert result.status_code == 201
    client.post("/auth/logout", headers=headers)
    assert (
        client.post(
            "/auth/login", json={"username": role, "password": "safe-test-password"}
        ).status_code
        == 200
    )
    return {"X-CSRF-Token": client.cookies["csrf"]}


def test_cookie_logout_and_csrf(client, headers):
    assert client.get("/auth/me").json()["role"] == "admin"
    assert (
        client.post("/incidents", json={"title": "Test case", "severity": "low"}).status_code == 403
    )
    response = client.post("/auth/logout", headers=headers)
    assert response.status_code == 204
    assert client.get("/auth/me").status_code == 401


def test_login_errors_and_throttle(client):
    for _ in range(10):
        assert (
            client.post(
                "/auth/login", json={"username": "missing", "password": "wrong"}
            ).status_code
            == 401
        )
    assert (
        client.post("/auth/login", json={"username": "missing", "password": "wrong"}).status_code
        == 429
    )


def test_viewer_denied(client, headers):
    h = account(client, headers, "viewer")
    assert client.get("/metrics").status_code == 200
    assert (
        client.post(
            "/incidents", headers=h, json={"title": "Test case", "severity": "low"}
        ).status_code
        == 403
    )
    assert client.patch("/incidents/1", headers=h, json={"status": "resolved"}).status_code == 403
    assert client.post("/incidents/1/notes", headers=h, json={"body": "test"}).status_code == 403
    assert (
        client.post(
            "/users",
            headers=h,
            json={"username": "abc", "password": "safe-test-password", "role": "admin"},
        ).status_code
        == 403
    )


def test_analyst_assignment_denied(client, headers):
    h = account(client, headers, "analyst")
    i = client.post("/incidents", headers=h, json={"title": "Test case", "severity": "low"}).json()[
        "id"
    ]
    assert client.patch(f"/incidents/{i}", headers=h, json={"assignee_id": 1}).status_code == 403
    assert (
        client.patch(f"/incidents/{i}", headers=h, json={"status": "investigating"}).status_code
        == 200
    )


def test_full_workflow(client, headers):
    i = client.post(
        "/incidents",
        headers=headers,
        json={"title": "Account compromise review", "severity": "high", "category": "identity"},
    ).json()["id"]
    assert (
        client.patch(
            f"/incidents/{i}", headers=headers, json={"severity": "critical", "assignee_id": 1}
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/incidents/{i}/notes",
            headers=headers,
            json={"body": "Account owner contacted; reset approved"},
        ).status_code
        == 201
    )
    assert client.get(f"/incidents/{i}/notes").json()[0]["author"] == "test.admin"
    assert (
        client.patch(f"/incidents/{i}", headers=headers, json={"status": "resolved"}).status_code
        == 200
    )
    history = client.get(f"/incidents/{i}/history").json()
    assert [e["action"] for e in history] == [
        "created",
        "severity_changed",
        "assignee_id_changed",
        "note_added",
        "status_changed",
    ]
    assert all(e["actor"] == "test.admin" for e in history)
    assert client.get("/metrics").json()["by_status"]["resolved"] == 1
    assert client.get("/metrics").json()["trends"][0]["count"] == 1
    assert client.get("/activity").json()[0]["action"] == "status_changed"


def test_search_sort_and_counts(client, headers):
    for title in ["Zulu report", "Alpha report", "Unrelated record"]:
        client.post(
            "/incidents",
            headers=headers,
            json={"title": title, "severity": "medium", "category": "Phishing"},
        )
    response = client.get("/incidents?q=report&sort=title&limit=1")
    assert response.headers["X-Total-Count"] == "2"
    assert response.json()[0]["title"] == "Alpha report"
    assert client.get("/incidents?category=Other").json() == []


def test_invalid_changes(client, headers):
    i = client.post(
        "/incidents", headers=headers, json={"title": "Test case", "severity": "low"}
    ).json()["id"]
    for payload in [
        {"status": None},
        {"severity": "extreme"},
        {"title": "  "},
        {"assignee_id": 999},
    ]:
        assert client.patch(f"/incidents/{i}", headers=headers, json=payload).status_code == 422
    assert (
        client.post(f"/incidents/{i}/notes", headers=headers, json={"body": " "}).status_code == 422
    )
    assert (
        client.post(
            "/incidents", headers=headers, json={"title": "   ", "severity": "low"}
        ).status_code
        == 422
    )
    assert client.get("/incidents?sort=unknown").status_code == 422


def test_origin_and_expiry(client, headers):
    assert (
        client.post(
            "/auth/login",
            headers={"Origin": "https://evil.example"},
            json={"username": "x", "password": "x"},
        ).status_code
        == 403
    )
    for db in app.dependency_overrides[get_db]():
        session = db.scalar(select(LoginSession))
        session.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    assert client.get("/auth/me").status_code == 401


def test_user_conflict_and_password_hash(client, headers):
    payload = {"username": "test.admin", "password": "another-test-password", "role": "admin"}
    assert client.post("/users", headers=headers, json=payload).status_code == 409
    payload["username"] = "new"
    payload["password"] = "short"
    assert client.post("/users", headers=headers, json=payload).status_code == 422
    response = client.post(
        "/auth/login", json={"username": "test.admin", "password": "test-password-123"}
    )
    assert "HttpOnly" in response.headers.get_list("set-cookie")[0]
    assert "password_hash" not in response.json()
