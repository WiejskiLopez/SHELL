"""Rename message → message_router and consolidate columns.

Revision ID: 059
Revises: 058
Create Date: 2026-07-14

* Drops legacy columns, renames table ``message`` → ``message_router``
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "059"
down_revision = "058"
branch_labels = None
depends_on = None


def _table_exists(name: str) -> bool:
    conn = op.get_bind()
    return conn.dialect.has_table(conn, name)


def upgrade() -> None:
    if not _table_exists("message"):
        op.create_table(
            "message_router",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("message_data", sa.JSON, nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        return

    op.drop_table("message")
    op.create_table(
        "message_router",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("message_data", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    if not _table_exists("message_router"):
        return

    op.drop_table("message_router")
    op.create_table(
        "message",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("message_type", sa.String(128), nullable=False, server_default=""),
        sa.Column("business_payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("source", sa.String(256), nullable=False, server_default=""),
        sa.Column("destination", sa.String(256), nullable=False, server_default=""),
        sa.Column("status", sa.String(32), nullable=False, server_default="created"),
        sa.Column("workflow_id", sa.String(36), nullable=True),
        sa.Column("step", sa.Integer, nullable=True),
        sa.Column("sequence_id", sa.Integer, nullable=True),
        sa.Column("source_node_execution_id", sa.String(36), nullable=True),
        sa.Column("target_node_execution_id", sa.String(36), nullable=True),
        sa.Column("source_role", sa.String(64), nullable=True),
        sa.Column("target_role", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
    )
