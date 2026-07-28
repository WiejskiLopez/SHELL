"""Add retry_count, last_attempted_at, error columns to inbox_event.

Revision ID: 065
Revises: 064
Create Date: 2026-07-28

* Add ``inbox_event.retry_count`` — integer, default 0
* Add ``inbox_event.last_attempted_at`` — nullable timestamp
* Add ``inbox_event.error`` — nullable text
* Create index ``ix_inbox_event_retryable`` for retry + backoff queries
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "065"
down_revision = "064"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("inbox_event") as batch:
        batch.add_column(sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False))
        batch.add_column(sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("error", sa.Text(), nullable=True))

    op.create_index("ix_inbox_event_retryable", "inbox_event", ["retry_count", "last_attempted_at"])


def downgrade() -> None:
    op.drop_index("ix_inbox_event_retryable", table_name="inbox_event")

    with op.batch_alter_table("inbox_event") as batch:
        batch.drop_column("error")
        batch.drop_column("last_attempted_at")
        batch.drop_column("retry_count")
