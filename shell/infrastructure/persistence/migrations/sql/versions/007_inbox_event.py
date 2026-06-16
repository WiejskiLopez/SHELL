"""Phase 15 — adds inbox_event table for Exactly-Once processing.

Revision ID: 007
Revises: 006
Create Date: 2026-06-15
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "inbox_event",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_inbox_event_type", "inbox_event", ["event_type"])
    op.create_index("ix_inbox_event_processed_at", "inbox_event", ["processed_at"])

def downgrade() -> None:
    op.drop_index("ix_inbox_event_processed_at", table_name="inbox_event")
    op.drop_index("ix_inbox_event_type", table_name="inbox_event")
    op.drop_table("inbox_event")