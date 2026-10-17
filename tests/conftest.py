"""Isolated in-memory database used in unit/integration tests."""

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from incidentops.db import Base, get_db
from incidentops.main import app, attempts
from incidentops.models import User
from incidentops.security import hasher


@pytest.fixture
def client():
    postgres_url = os.getenv("TEST_DATABASE_URL")
    schema = "incidentops_test_" + uuid4().hex
    owner = None
    if postgres_url:
        owner = create_engine(postgres_url)
        if owner.dialect.name != "postgresql":
            raise ValueError("TEST_DATABASE_URL must use PostgreSQL")
        with owner.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(postgres_url, connect_args={"options": f"-csearch_path={schema}"})
    else:
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
        if owner is not None:
            with owner.begin() as connection:
                connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            owner.dispose()


@pytest.fixture
def headers(client):
    response = client.post(
        "/auth/login", json={"username": "test.admin", "password": "test-password-123"}
    )
    assert response.status_code == 200
    return {"X-CSRF-Token": client.cookies["csrf"]}
