"""Phase 23 — add sub-graph fields to graph_execution and node_execution.

Revision ID: 015
Revises: 014
Create Date: 2026-06-19

* Add parent_graph_execution_id, parent_tasker_node_execution_id,
  state_input, state_output, depth, timeout_at, correlation_id, tags
  to ``graph_execution``.
* Add sub_graph_definition_id, sub_graph_definition_version,
  timeout_seconds, max_retries, retry_delay_seconds to ``node_execution``.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── graph_execution ────────────────────────────────────────────────────
    with op.batch_alter_table("graph_execution") as batch:
        batch.add_column(
            sa.Column("parent_graph_execution_id", sa.String(36), nullable=True),
        )
        batch.add_column(
            sa.Column("parent_tasker_node_execution_id", sa.String(36), nullable=True),
        )
        batch.add_column(
            sa.Column("state_input", sa.JSON, nullable=False, server_default="{}"),
        )
        batch.add_column(
            sa.Column("state_output", sa.JSON, nullable=False, server_default="{}"),
        )
        batch.add_column(
            sa.Column("depth", sa.Integer, nullable=False, server_default="0"),
        )
        batch.add_column(
            sa.Column("timeout_at", sa.DateTime, nullable=True),
        )
        batch.add_column(
            sa.Column("correlation_id", sa.String(255), nullable=False, server_default=""),
        )
        batch.add_column(
            sa.Column("tags", sa.JSON, nullable=False, server_default="{}"),
        )
        batch.create_index(
            "ix_graph_execution_parent_graph_execution_id",
            ["parent_graph_execution_id"],
        )
        batch.create_index(
            "ix_graph_execution_parent_tasker_node_execution_id",
            ["parent_tasker_node_execution_id"],
        )
        batch.create_foreign_key(
            "fk_graph_execution_parent",
            "graph_execution",
            ["parent_graph_execution_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # ── node_execution ───────────────────────────────────────────────
    with op.batch_alter_table("node_execution") as batch:
        batch.add_column(
            sa.Column("sub_graph_definition_id", sa.String(36), nullable=True),
        )
        batch.add_column(
            sa.Column("sub_graph_definition_version", sa.Integer, nullable=True),
        )
        batch.add_column(
            sa.Column("timeout_seconds", sa.Integer, nullable=False, server_default="0"),
        )
        batch.add_column(
            sa.Column("max_retries", sa.Integer, nullable=False, server_default="0"),
        )
        batch.add_column(
            sa.Column("retry_delay_seconds", sa.Integer, nullable=False, server_default="0"),
        )


def downgrade() -> None:
    # ── node_execution ───────────────────────────────────────────────
    with op.batch_alter_table("node_execution") as batch:
        batch.drop_column("retry_delay_seconds")
        batch.drop_column("max_retries")
        batch.drop_column("timeout_seconds")
        batch.drop_column("sub_graph_definition_version")
        batch.drop_column("sub_graph_definition_id")

    # ── graph_execution ────────────────────────────────────────────────────
    with op.batch_alter_table("graph_execution") as batch:
        batch.drop_constraint("fk_graph_execution_parent", type_="foreignkey")
        batch.drop_index("ix_graph_execution_parent_tasker_node_execution_id")
        batch.drop_index("ix_graph_execution_parent_graph_execution_id")
        batch.drop_column("tags")
        batch.drop_column("correlation_id")
        batch.drop_column("timeout_at")
        batch.drop_column("depth")
        batch.drop_column("state_output")
        batch.drop_column("state_input")
        batch.drop_column("parent_tasker_node_execution_id")
        batch.drop_column("parent_graph_execution_id")
