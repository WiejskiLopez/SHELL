"""Add message, outbox_message, inbox_message tables.

Revision ID: 039
Revises: 038
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "039"
down_revision = "038"
branch_labels = None
depends_on = None


def _table_exists(name: str) -> bool:
    conn = op.get_bind()
    return conn.dialect.has_table(conn, name)


def upgrade() -> None:
    if not _table_exists("message"):
        op.create_table(
            "message",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("message_type", sa.String(128), nullable=False),
            sa.Column("business_payload", sa.JSON, nullable=False, server_default="{}"),
            sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
            sa.Column("source", sa.String(256), nullable=False),
            sa.Column("destination", sa.String(256), nullable=False),
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
        op.create_index("ix_message_workflow_id", "message", ["workflow_id"])
        op.create_index("ix_message_source", "message", ["source"])
        op.create_index("ix_message_destination", "message", ["destination"])
        op.create_index("ix_message_status", "message", ["status"])

    if not _table_exists("outbox_message"):
        op.create_table(
            "outbox_message",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("envelope", sa.JSON, nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_outbox_message_published_at", "outbox_message", ["published_at"])

    if not _table_exists("inbox_message"):
        op.create_table(
            "inbox_message",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("envelope", sa.JSON, nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("error", sa.Text, nullable=True),
        )
        op.create_index("ix_inbox_message_processed_at", "inbox_message", ["processed_at"])


def downgrade() -> None:
    op.drop_index("ix_inbox_message_processed_at", table_name="inbox_message")
    op.drop_table("inbox_message")
    op.drop_index("ix_outbox_message_published_at", table_name="outbox_message")
    op.drop_table("outbox_message")
    op.drop_index("ix_message_status", table_name="message")
    op.drop_index("ix_message_destination", table_name="message")
    op.drop_index("ix_message_source", table_name="message")
    op.drop_index("ix_message_workflow_id", table_name="message")
    op.drop_table("message")
