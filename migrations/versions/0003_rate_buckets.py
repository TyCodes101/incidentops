"""Shared production login and demonstration quotas."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"


def upgrade():
    op.create_table(
        "rate_buckets",
        sa.Column("key", sa.String(160), primary_key=True),
        sa.Column("count", sa.Integer, nullable=False),
        sa.Column("expires", sa.Integer, nullable=False),
    )
    op.create_index("ix_rate_buckets_expires", "rate_buckets", ["expires"])


def downgrade():
    op.drop_index("ix_rate_buckets_expires", table_name="rate_buckets")
    op.drop_table("rate_buckets")
