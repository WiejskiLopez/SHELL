"""Phase 21 — add graph_node_transition table for edge-based orchestration.

Revision ID: 013
Revises: 012
Create Date: 2026-06-19

* Create ``graph_node_transition`` table — defines transitions between graph nodes.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "graph_node_transition",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "graph_execution_id",
            sa.String(36),
            sa.ForeignKey("graph_execution.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "source_node_execution_id",
            sa.String(36),
            sa.ForeignKey("graph_node_execution.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "target_node_execution_id",
            sa.String(36),
            sa.ForeignKey("graph_node_execution.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("transition_type", sa.String(20), nullable=False, server_default="sequence"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("condition_expression", sa.Text, nullable=True),
        sa.Column("condition_language", sa.String(20), nullable=True),
        sa.Column("join_wait_count", sa.Integer, nullable=True),
        sa.Column("max_loop_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("timeout_seconds", sa.Integer, nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("retry_delay_seconds", sa.Integer, nullable=False, server_default="0"),
        sa.Column("data_mapping", sa.JSON, nullable=True),
        sa.Column("label", sa.String(255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("graph_node_transition")
