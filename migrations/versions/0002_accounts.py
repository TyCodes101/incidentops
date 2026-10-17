"""Accounts, sessions, assignments, actor attribution, investigation notes."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(80), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
    )
    op.create_table(
        "sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("incident_id", sa.Integer, sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column("author", sa.String(80), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    with op.batch_alter_table("incidents") as batch:
        batch.add_column(sa.Column("assignee_id", sa.Integer))
        batch.create_foreign_key("fk_incident_owner", "users", ["assignee_id"], ["id"])
    op.add_column(
        "incident_events",
        sa.Column("actor", sa.String(80), nullable=False, server_default="system"),
    )


def downgrade():
    op.drop_column("incident_events", "actor")
    with op.batch_alter_table("incidents") as batch:
        batch.drop_constraint("fk_incident_owner", type_="foreignkey")
        batch.drop_column("assignee_id")
    for table in ["notes", "sessions", "users"]:
        op.drop_table(table)
