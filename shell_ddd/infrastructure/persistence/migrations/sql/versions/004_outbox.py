"""Faza 12 — adds outbox_event table.

Revision ID: 004
Revises: 003
Create Date: 2026-06-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox_event",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_outbox_event_type", "outbox_event", ["event_type"])
    op.create_index("ix_outbox_event_published_at", "outbox_event", ["published_at"])


def downgrade() -> None:
    op.drop_index("ix_outbox_event_published_at", table_name="outbox_event")
    op.drop_index("ix_outbox_event_type", table_name="outbox_event")
    op.drop_table("outbox_event")
