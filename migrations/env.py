from alembic import context

from incidentops import models  # noqa: F401
from incidentops.db import Base, engine

with engine.connect() as connection:
    # SQLite batch table recreation must temporarily suspend referencing FKs.
    if connection.dialect.name == "sqlite":
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.commit()
    context.configure(connection=connection, target_metadata=Base.metadata, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()
    if connection.dialect.name == "sqlite":
        violations = connection.exec_driver_sql("PRAGMA foreign_key_check").all()
        if violations:
            raise RuntimeError(f"Foreign key violations after migration: {violations}")
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
