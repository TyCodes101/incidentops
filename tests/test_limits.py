from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from incidentops.db import Base
from incidentops.limits import consume
from incidentops.models import RateBucket


def test_shared_quota_on_configured_database(client):
    from incidentops.db import get_db
    from incidentops.main import app

    for db in app.dependency_overrides[get_db]():
        engine = db.bind
    for _ in range(2):
        with Session(engine) as db:
            consume(db, "shared", "worker", 2, 60, now=120)
    with Session(engine) as db:
        with pytest.raises(HTTPException) as exc:
            consume(db, "shared", "worker", 2, 60, now=121)
        assert exc.value.status_code == 429


def test_quota_persists_across_sessions_and_resets(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'limits.db'}")
    Base.metadata.create_all(engine)
    for _ in range(2):
        with Session(engine) as db:
            consume(db, "test", "client", 2, 60, now=120)
    with Session(engine) as db:
        with pytest.raises(HTTPException) as exc:
            consume(db, "test", "client", 2, 60, now=121)
        assert exc.value.status_code == 429
        assert exc.value.headers["Retry-After"] == "59"
        consume(db, "test", "client", 2, 60, now=181)
        assert len(db.scalars(select(RateBucket)).all()) == 1
    engine.dispose()


def test_concurrent_workers_cannot_exceed_quota(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'concurrent.db'}")
    Base.metadata.create_all(engine)

    def attempt(_):
        with Session(engine) as db:
            try:
                consume(db, "test", "shared", 5, 60, now=120)
                return True
            except HTTPException:
                return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(20))) == 5
    engine.dispose()
