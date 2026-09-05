from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "saga_0002_create_timeout"
down_revision = "saga_0001_create_instance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saga_timeout",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("saga_id", sa.String(), nullable=False),
        sa.Column("saga_key", sa.String(), nullable=False),
        sa.Column("step", sa.String(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_saga_timeout_status_due", "saga_timeout", ["status", "due_at"])


def downgrade() -> None:
    op.drop_index("ix_saga_timeout_status_due", table_name="saga_timeout")
    op.drop_table("saga_timeout")
