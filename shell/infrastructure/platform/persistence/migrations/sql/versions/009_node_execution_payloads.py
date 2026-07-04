"""Phase 17 — adds node_execution_input_payload and output_payload tables.

Revision ID: 009
Revises: 008
Create Date: 2026-06-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "node_execution_input_payload",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "node_execution_id",
            sa.String(36),
            sa.ForeignKey("node_execution.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_node_execution_input_payload_node_execution_id",
        "node_execution_input_payload",
        ["node_execution_id"],
    )
    op.create_index(
        "uq_node_execution_input_payload_is_current",
        "node_execution_input_payload",
        ["node_execution_id"],
        postgresql_where=sa.text("is_current = true"),
        sqlite_where=sa.text("is_current = 1"),
        unique=True,
    )

    op.create_table(
        "node_execution_output_payload",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "node_execution_id",
            sa.String(36),
            sa.ForeignKey("node_execution.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_node_execution_output_payload_node_execution_id",
        "node_execution_output_payload",
        ["node_execution_id"],
    )
    op.create_index(
        "uq_node_execution_output_payload_is_current",
        "node_execution_output_payload",
        ["node_execution_id"],
        postgresql_where=sa.text("is_current = true"),
        sqlite_where=sa.text("is_current = 1"),
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_node_execution_output_payload_is_current",
        table_name="node_execution_output_payload",
    )
    op.drop_index(
        "ix_node_execution_output_payload_node_execution_id",
        table_name="node_execution_output_payload",
    )
    op.drop_table("node_execution_output_payload")
    op.drop_index(
        "uq_node_execution_input_payload_is_current",
        table_name="node_execution_input_payload",
    )
    op.drop_index(
        "ix_node_execution_input_payload_node_execution_id",
        table_name="node_execution_input_payload",
    )
    op.drop_table("node_execution_input_payload")
