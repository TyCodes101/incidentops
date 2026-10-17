"""Atomic fixed-window quotas shared by all production workers."""

import hashlib
import time

from fastapi import HTTPException
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from incidentops.models import RateBucket


def consume(db, scope, identity, limit, seconds, *, now=None):
    now = int(time.time() if now is None else now)
    window = now // seconds
    identity_hash = hashlib.sha256(str(identity).encode()).hexdigest()
    key = f"{scope}:{identity_hash}:{window}"
    insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    db.execute(delete(RateBucket).where(RateBucket.expires < now))
    statement = (
        insert(RateBucket)
        .values(key=key, count=1, expires=(window + 1) * seconds)
        .on_conflict_do_update(
            index_elements=[RateBucket.key],
            set_={"count": RateBucket.count + 1},
            where=RateBucket.count < limit,
        )
        .returning(RateBucket.count)
    )
    accepted = db.scalar(statement)
    # Commit quota consumption independently of the subsequent operation's success.
    db.commit()
    if accepted is None:
        raise HTTPException(
            429,
            "Request limit reached; retry after the current window",
            headers={"Retry-After": str((window + 1) * seconds - now)},
        )
