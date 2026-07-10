"""Phase 22 — split node_transition into execution and definition tables.

Revision ID: 014
Revises: 013
Create Date: 2026-06-19

* Rename ``node_transition`` → ``node_transition_execution``
  (execution-side transitions, referencing graph_execution / node_execution).
* Create ``node_transition_definition`` table — template transitions
  referencing graph_definition / node_definition.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("node_transition", "node_transition_execution")

    op.create_table(
        "node_transition_definition",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "graph_definition_id",
            sa.String(36),
            sa.ForeignKey("graph_definition.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "source_node_definition_id",
            sa.String(36),
            sa.ForeignKey("node_definition.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "target_node_definition_id",
            sa.String(36),
            sa.ForeignKey("node_definition.id", ondelete="CASCADE"),
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
    op.drop_table("node_transition_definition")
    op.rename_table("node_transition_execution", "node_transition")
