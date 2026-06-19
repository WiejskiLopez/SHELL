"""Phase 19 — add status to task_execution and graph, create graph_execution_state.

Revision ID: 011
Revises: 010
Create Date: 2026-06-19
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- task_execution.status ---
    with op.batch_alter_table("task_execution") as batch:
        batch.add_column(
            sa.Column("status", sa.String(20), nullable=False, server_default="PENDING")
        )

    # --- graph_execution.status ---
    with op.batch_alter_table("graph_execution") as batch:
        batch.add_column(
            sa.Column("status", sa.String(20), nullable=False, server_default="RUNNING")
        )

    # --- graph_execution_state table ---
    op.create_table(
        "graph_execution_state",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "graph_execution_id",
            sa.String(36),
            sa.ForeignKey("graph_execution.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_graph_execution_state_graph_id",
        "graph_execution_state",
        ["graph_execution_id"],
    )
    op.create_index(
        "uq_graph_execution_state_current",
        "graph_execution_state",
        ["graph_execution_id"],
        postgresql_where=sa.text("is_current = true"),
        sqlite_where=sa.text("is_current = 1"),
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_graph_execution_state_current", table_name="graph_execution_state")
    op.drop_index("ix_graph_execution_state_graph_id", table_name="graph_execution_state")
    op.drop_table("graph_execution_state")

    with op.batch_alter_table("graph_execution") as batch:
        batch.drop_column("status")

    with op.batch_alter_table("task_execution") as batch:
        batch.drop_column("status")
