"""Faza 11 — adds audit_event table.

Revision ID: 003
Revises: 002
Create Date: 2026-06-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_event",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
    )
    op.create_index("ix_audit_event_type", "audit_event", ["event_type"])
    op.create_index("ix_audit_event_occurred_at", "audit_event", ["occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_event_occurred_at", table_name="audit_event")
    op.drop_index("ix_audit_event_type", table_name="audit_event")
    op.drop_table("audit_event")
