import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text


def test_migrations_preserve_starter_records(tmp_path):
    root = Path(__file__).resolve().parents[1]
    url = "sqlite:///" + (tmp_path / "migrate.db").as_posix()
    env = {**os.environ, "DATABASE_URL": url}

    def run(*args):
        subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=root,
            env=env,
            check=True,
            capture_output=True,
            stdin=subprocess.DEVNULL,
        )

    run("upgrade", "0001")
    engine = create_engine(url)
    with engine.begin() as db:
        db.execute(
            text(
                "INSERT INTO incidents (id,title,description,severity,status,category) VALUES (1,'Preserved case','Existing record','high','open','identity')"
            )
        )
    with engine.begin() as db:
        db.execute(
            text(
                "INSERT INTO incident_events (id, incident_id, action, detail) VALUES (1,1,'created','Preserve history')"
            )
        )
    engine.dispose()
    run("upgrade", "head")
    run("upgrade", "head")
    engine = create_engine(url)
    assert {"users", "notes", "sessions", "incidents", "incident_events"} <= set(
        inspect(engine).get_table_names()
    )
    with engine.connect() as db:
        assert (
            db.execute(text("SELECT title FROM incidents WHERE id=1")).scalar() == "Preserved case"
        )
    with engine.connect() as db:
        assert (
            db.execute(text("SELECT detail FROM incident_events WHERE id=1")).scalar()
            == "Preserve history"
        )
    engine.dispose()
    run("downgrade", "0001")
    run("upgrade", "head")
