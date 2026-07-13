"""Consolidate graph_execution_state_input / _output into single graph_execution_state table with direction column.

Revision ID: 057
Revises: 056
Create Date: 2026-07-13

* Create ``graph_execution_state`` table with ``direction`` discriminator column
* Drop ``graph_execution_state_input`` table
* Drop ``graph_execution_state_output`` table
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "057"
down_revision = "056"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "graph_execution_state",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "graph_execution_id",
            sa.String(36),
            sa.ForeignKey("graph_execution.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("state_data", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_graph_execution_state_graph_execution_id",
        "graph_execution_state",
        ["graph_execution_id"],
    )
    op.create_index(
        "uq_graph_execution_state_graph_execution_id_direction",
        "graph_execution_state",
        ["graph_execution_id", "direction"],
        unique=True,
    )

    # Drop old tables (no data migration needed — test/seed env)
    op.drop_table("graph_execution_state_output")
    op.drop_table("graph_execution_state_input")


def downgrade() -> None:
    # Recreate input table
    op.create_table(
        "graph_execution_state_input",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "graph_execution_id",
            sa.String(36),
            sa.ForeignKey("graph_execution.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("state_data", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_graph_execution_state_input_graph_execution_id",
        "graph_execution_state_input",
        ["graph_execution_id"],
    )

    # Recreate output table
    op.create_table(
        "graph_execution_state_output",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "graph_execution_id",
            sa.String(36),
            sa.ForeignKey("graph_execution.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("state_data", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_graph_execution_state_output_graph_execution_id",
        "graph_execution_state_output",
        ["graph_execution_id"],
    )

    op.drop_table("graph_execution_state")
