import os
import subprocess
import sys

from fastapi.testclient import TestClient


def test_vercel_adapter_preserves_authenticated_api(client):
    from server import app

    with TestClient(app) as hosted:
        assert hosted.get("/api/health").json() == {"status": "ok"}
        assert hosted.get("/api/incidents").status_code == 401
        result = hosted.post(
            "/api/auth/login", json={"username": "test.admin", "password": "test-password-123"}
        )
        assert result.status_code == 200
        assert hosted.get("/api/auth/me").json()["role"] == "admin"
        assert hosted.post("/api/incidents", json={}).status_code == 403
        assert (
            hosted.post(
                "/api/auth/logout", headers={"X-CSRF-Token": hosted.cookies["csrf"]}
            ).status_code
            == 204
        )
        assert hosted.get("/api/auth/me").status_code == 401


def test_vercel_adapter_serves_declared_frontend_assets(client, tmp_path, monkeypatch):
    from server import app

    monkeypatch.chdir(tmp_path)
    assets = tmp_path / "frontend" / "dist"
    assets.mkdir(parents=True)
    (assets / "index.html").write_text("<!doctype html><title>Test frontend</title>")
    (assets / "app.js").write_text("console.log('fixture')")
    with TestClient(app) as hosted:
        assert hosted.get("/").status_code == 200
        assert "Test frontend" in hosted.get("/").text
        assert hosted.get("/app.js").status_code == 200
        assert hosted.get("/api/health").json() == {"status": "ok"}
        assert hosted.get("/missing.js").status_code == 404
        assert hosted.get("/../pyproject.toml").status_code == 404


def test_public_seed_has_no_admin_and_is_opt_in(tmp_path):
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    from incidentops.db import Base
    from incidentops.models import Incident, User

    url = f"sqlite:///{tmp_path / 'public-demo.db'}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    env = {**os.environ, "DATABASE_URL": url, "APP_ENV": "development", "PUBLIC_DEMO": "0"}

    def seed():
        return subprocess.run(
            [sys.executable, "-m", "incidentops.manage", "public-demo"],
            env=env,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=30,
        )

    assert seed().returncode != 0
    env["PUBLIC_DEMO"] = "1"
    assert seed().returncode == 0
    assert seed().returncode == 0
    with Session(engine) as db:
        assert sorted(db.scalars(select(User.role))) == ["analyst", "viewer"]
        assert len(db.scalars(select(Incident)).all()) == 12
    engine.dispose()


def test_public_demo_writer_quota(client, headers, monkeypatch):
    monkeypatch.setenv("PUBLIC_DEMO", "1")
    for _ in range(30):
        assert (
            client.post("/analyzer", headers=headers, json={"csv_text": "invalid"}).status_code
            == 422
        )
    result = client.post("/analyzer", headers=headers, json={"csv_text": "invalid"})
    assert result.status_code == 429
    assert int(result.headers["Retry-After"]) > 0
    assert client.get("/incidents").status_code == 200
