"""Isolated in-memory database used in unit/integration tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from incidentops.db import Base, get_db
from incidentops.main import app, attempts
from incidentops.models import User
from incidentops.security import hasher


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    with Session() as db:
        db.add(
            User(
                username="test.admin", password_hash=hasher.hash("test-password-123"), role="admin"
            )
        )
        db.commit()
    attempts.clear()

    def override_db():
        with Session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def headers(client):
    response = client.post(
        "/auth/login", json={"username": "test.admin", "password": "test-password-123"}
    )
    assert response.status_code == 200
    return {"X-CSRF-Token": client.cookies["csrf"]}
