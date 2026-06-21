"""Phase 22 — split graph_execution_state into input and output tables.

Revision ID: 022
Revises: 021
Create Date: 2026-06-21

* Create ``graph_execution_state_input`` table (same structure as ``graph_execution_state``).
* Create ``graph_execution_state_output`` table (same structure as ``graph_execution_state``).
* Drop ``graph_execution_state`` table.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- graph_execution_state_input table ---
    op.create_table(
        "graph_execution_state_input",
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
        "ix_graph_execution_state_input_graph_execution_id",
        "graph_execution_state_input",
        ["graph_execution_id"],
    )
    op.create_index(
        "uq_graph_execution_state_input_is_current",
        "graph_execution_state_input",
        ["graph_execution_id"],
        postgresql_where=sa.text("is_current = true"),
        sqlite_where=sa.text("is_current = 1"),
        unique=True,
    )

    # --- graph_execution_state_output table ---
    op.create_table(
        "graph_execution_state_output",
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
        "ix_graph_execution_state_output_graph_execution_id",
        "graph_execution_state_output",
        ["graph_execution_id"],
    )
    op.create_index(
        "uq_graph_execution_state_output_is_current",
        "graph_execution_state_output",
        ["graph_execution_id"],
        postgresql_where=sa.text("is_current = true"),
        sqlite_where=sa.text("is_current = 1"),
        unique=True,
    )

    # --- drop old table ---
    op.drop_index("uq_graph_execution_state_is_current", table_name="graph_execution_state")
    op.drop_index("ix_graph_execution_state_graph_execution_id", table_name="graph_execution_state")
    op.drop_table("graph_execution_state")


def downgrade() -> None:
    # --- recreate old table ---
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
        "ix_graph_execution_state_graph_execution_id",
        "graph_execution_state",
        ["graph_execution_id"],
    )
    op.create_index(
        "uq_graph_execution_state_is_current",
        "graph_execution_state",
        ["graph_execution_id"],
        postgresql_where=sa.text("is_current = true"),
        sqlite_where=sa.text("is_current = 1"),
        unique=True,
    )

    # --- drop new tables ---
    op.drop_index("uq_graph_execution_state_output_is_current", table_name="graph_execution_state_output")
    op.drop_index("ix_graph_execution_state_output_graph_execution_id", table_name="graph_execution_state_output")
    op.drop_table("graph_execution_state_output")

    op.drop_index("uq_graph_execution_state_input_is_current", table_name="graph_execution_state_input")
    op.drop_index("ix_graph_execution_state_input_graph_execution_id", table_name="graph_execution_state_input")
    op.drop_table("graph_execution_state_input")
