"""Regression tests for release security boundaries and extreme CSV dates."""

import asyncio
import json
from datetime import timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from incidentops.analyzer import analyze
from incidentops.config import validate_environment
from incidentops.db import get_db
from incidentops.http import RequestSizeLimit
from incidentops.main import app
from incidentops.models import LoginSession, utcnow
from incidentops.security import digest


def test_chunked_body_stops_before_consuming_the_entire_upload():
    async def exercise():
        consumed = 0
        called = False
        sent = []

        async def receive():
            nonlocal consumed
            consumed += 1
            return {"type": "http.request", "body": b"x" * 32768, "more_body": True}

        async def downstream(scope, receive, send):
            nonlocal called
            called = True

        async def send(message):
            sent.append(message)

        await RequestSizeLimit(downstream)(
            {"type": "http", "method": "POST", "headers": []}, receive, send
        )
        assert consumed == 3
        assert not called
        assert sent[0]["status"] == 413
        assert json.loads(sent[1]["body"]) == {"detail": "Request too large"}

    asyncio.run(exercise())


def test_declared_oversized_body_is_rejected_without_reading():
    async def exercise():
        sent = []

        async def receive():
            raise AssertionError("An oversized declared body must not be buffered")

        async def downstream(scope, receive, send):
            raise AssertionError("Oversized input must not reach the application")

        async def send(message):
            sent.append(message)

        await RequestSizeLimit(downstream)(
            {"type": "http", "method": "POST", "headers": [(b"content-length", b"65537")]},
            receive,
            send,
        )
        assert sent[0]["status"] == 413

    asyncio.run(exercise())


def test_exact_body_limit_is_replayed_unchanged():
    async def exercise():
        async def receive():
            return {"type": "http.request", "body": b"x" * 65536, "more_body": False}

        async def downstream(scope, receive, send):
            assert (await receive())["body"] == b"x" * 65536

        async def send(message):
            raise AssertionError("The limit should not emit a response for an allowed body")

        await RequestSizeLimit(downstream)(
            {"type": "http", "method": "POST", "headers": []}, receive, send
        )

    asyncio.run(exercise())


def test_production_cookie_flags_and_https_session(client, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_ORIGIN", "https://testserver")
    client.base_url = "https://testserver"
    response = client.post(
        "/auth/login", json={"username": "test.admin", "password": "test-password-123"}
    )
    assert response.status_code == 200
    cookies = response.headers.get_list("set-cookie")
    assert all("Secure" in cookie and "SameSite=strict" in cookie for cookie in cookies)
    assert "HttpOnly" in next(cookie for cookie in cookies if cookie.startswith("session="))
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000"
    assert client.get("/auth/me").status_code == 200
    assert (
        client.post("/auth/logout", headers={"X-CSRF-Token": client.cookies["csrf"]}).status_code
        == 204
    )
    assert client.get("/auth/me").status_code == 401


def test_development_demo_account_is_not_usable_in_production(client, headers, monkeypatch):
    assert (
        client.post(
            "/users",
            headers=headers,
            json={"username": "demo.admin", "password": "Demo-Only-Change-Me!", "role": "admin"},
        ).status_code
        == 201
    )
    client.post("/auth/logout", headers=headers)
    monkeypatch.setenv("APP_ENV", "production")
    assert (
        client.post(
            "/auth/login", json={"username": "demo.admin", "password": "Demo-Only-Change-Me!"}
        ).status_code
        == 401
    )


def test_login_cleans_expired_sessions(client):
    for db in app.dependency_overrides[get_db]():
        db.add(
            LoginSession(
                token_hash=digest("expired-test-token"),
                user_id=1,
                expires_at=utcnow() - timedelta(days=1),
            )
        )
        db.commit()
    assert (
        client.post(
            "/auth/login", json={"username": "test.admin", "password": "test-password-123"}
        ).status_code
        == 200
    )
    for db in app.dependency_overrides[get_db]():
        assert db.get(LoginSession, digest("expired-test-token")) is None
        assert len(db.scalars(select(LoginSession)).all()) == 1


def test_concurrent_username_conflict_returns_409(client, headers, monkeypatch):
    original = app.dependency_overrides[get_db]

    def failing_commit():
        for db in original():

            def conflict():
                raise IntegrityError("duplicate username", {}, Exception("constraint"))

            monkeypatch.setattr(db, "commit", conflict)
            yield db

    app.dependency_overrides[get_db] = failing_commit
    response = client.post(
        "/users",
        headers=headers,
        json={"username": "racing-user", "password": "synthetic-password-42", "role": "viewer"},
    )
    assert response.status_code == 409
    assert response.json() == {"detail": "Username already exists"}


def test_minimum_valid_csv_timestamp_does_not_overflow():
    csv = "timestamp,username,source_ip,success\n" + "\n".join(
        "0001-01-01T00:00:00Z,fictional.user,192.0.2.1,false" for _ in range(5)
    )
    assert analyze(csv)["flags"][0]["failure_count"] == 5


@pytest.mark.parametrize(
    "origin",
    [
        "",
        "http://demo.example",
        "https://demo.example/",
        "https://demo.example/path",
        "https://user:pass@demo.example",
    ],
)
def test_production_rejects_unsafe_origin_configuration(monkeypatch, origin):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://test@localhost/test")
    monkeypatch.setenv("APP_ORIGIN", origin)
    with pytest.raises(ValueError, match="HTTPS origin"):
        validate_environment()


def test_production_requires_postgresql(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_ORIGIN", "https://demo.example")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///unintended.db")
    with pytest.raises(ValueError, match="PostgreSQL"):
        validate_environment()


def test_production_accepts_explicit_configuration(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_ORIGIN", "https://demo.example")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://test@db/test")
    validate_environment()


def test_login_rate_cache_has_a_bounded_number_of_clients(client):
    from collections import deque

    from incidentops.main import MAX_LOGIN_CLIENTS, attempts

    for number in range(MAX_LOGIN_CLIENTS):
        attempts[f"old-client-{number}"] = deque()
    assert (
        client.post("/auth/login", json={"username": "missing", "password": "wrong"}).status_code
        == 401
    )
    assert len(attempts) == MAX_LOGIN_CLIENTS
    assert "old-client-0" not in attempts


def test_password_verification_concurrency_is_bounded(monkeypatch):
    import time
    from concurrent.futures import ThreadPoolExecutor
    from threading import Lock

    from incidentops.security import hasher, verify

    state = {"active": 0, "peak": 0}
    lock = Lock()

    def expensive_check(hashed, password):
        with lock:
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
        time.sleep(0.03)
        with lock:
            state["active"] -= 1
        return True

    monkeypatch.setattr(
        type(hasher), "verify", lambda self, hashed, password: expensive_check(hashed, password)
    )
    with ThreadPoolExecutor(max_workers=6) as executor:
        assert all(executor.map(lambda _: verify("test-password", "test-hash"), range(6)))
    assert state["peak"] <= 2
    assert state["active"] == 0


def test_postgres_session_expiry_preserves_database_timezone(client, headers):
    from sqlalchemy import text

    for db in app.dependency_overrides[get_db]():
        if db.bind.dialect.name != "postgresql":
            pytest.skip("Requires the real PostgreSQL verification job")
        db.execute(text("SET TIME ZONE 'Pacific/Auckland'"))
        db.commit()
        session = db.get(LoginSession, digest(client.cookies["session"]))
        session.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    assert client.get("/auth/me").status_code == 401
