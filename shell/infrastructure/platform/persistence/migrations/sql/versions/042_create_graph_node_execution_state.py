"""Create graph_node_execution_state table for consolidated node state storage.

Revision ID: 042
Revises: 041
Create Date: 2026-06-28

* Create ``graph_node_execution_state`` table
* Migrate data from ``graph_node_execution_state_input`` (direction=INPUT)
* Migrate data from ``graph_node_execution_state_output`` (direction=OUTPUT)
* Drop old ``graph_node_execution_state_input`` and ``graph_node_execution_state_output`` tables
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "042"
down_revision = "041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "graph_node_execution_state",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "graph_node_execution_id",
            sa.String(36),
            sa.ForeignKey("graph_node_execution.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("state_data", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_graph_node_execution_state_graph_node_execution_id",
        "graph_node_execution_state",
        ["graph_node_execution_id"],
    )
    op.create_index(
        "uq_graph_node_execution_state_gnode_id_direction_current",
        "graph_node_execution_state",
        ["graph_node_execution_id", "direction"],
        postgresql_where=sa.text("is_current = true"),
        sqlite_where=sa.text("is_current = 1"),
        unique=True,
    )

    op.execute(
        """INSERT INTO graph_node_execution_state (id, graph_node_execution_id, direction, state_data, is_current, created_at)
           SELECT id, graph_node_execution_id, 'INPUT', payload, is_current, created_at
           FROM graph_node_execution_state_input"""
    )
    op.execute(
        """INSERT INTO graph_node_execution_state (id, graph_node_execution_id, direction, state_data, is_current, created_at)
           SELECT id, graph_node_execution_id, 'OUTPUT', payload, is_current, created_at
           FROM graph_node_execution_state_output"""
    )

    op.drop_index(
        "uq_graph_node_execution_output_payload_is_current",
        table_name="graph_node_execution_state_output",
    )
    op.drop_index(
        "ix_graph_node_execution_output_payload_graph_node_execution_id",
        table_name="graph_node_execution_state_output",
    )
    op.drop_table("graph_node_execution_state_output")

    op.drop_index(
        "uq_graph_node_execution_input_payload_is_current",
        table_name="graph_node_execution_state_input",
    )
    op.drop_index(
        "ix_graph_node_execution_input_payload_graph_node_execution_id",
        table_name="graph_node_execution_state_input",
    )
    op.drop_table("graph_node_execution_state_input")


def downgrade() -> None:
    op.create_table(
        "graph_node_execution_state_input",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "graph_node_execution_id",
            sa.String(36),
            sa.ForeignKey("graph_node_execution.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_graph_node_execution_state_input_graph_node_execution_id",
        "graph_node_execution_state_input",
        ["graph_node_execution_id"],
    )
    op.create_index(
        "uq_graph_node_execution_state_input_is_current",
        "graph_node_execution_state_input",
        ["graph_node_execution_id"],
        postgresql_where=sa.text("is_current = true"),
        sqlite_where=sa.text("is_current = 1"),
        unique=True,
    )
    op.create_table(
        "graph_node_execution_state_output",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "graph_node_execution_id",
            sa.String(36),
            sa.ForeignKey("graph_node_execution.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_graph_node_execution_state_output_graph_node_execution_id",
        "graph_node_execution_state_output",
        ["graph_node_execution_id"],
    )
    op.create_index(
        "uq_graph_node_execution_state_output_is_current",
        "graph_node_execution_state_output",
        ["graph_node_execution_id"],
        postgresql_where=sa.text("is_current = true"),
        sqlite_where=sa.text("is_current = 1"),
        unique=True,
    )

    op.execute(
        """INSERT INTO graph_node_execution_state_input (id, graph_node_execution_id, payload, is_current, created_at)
           SELECT id, graph_node_execution_id, state_data, is_current, created_at
           FROM graph_node_execution_state WHERE direction = 'INPUT'"""
    )
    op.execute(
        """INSERT INTO graph_node_execution_state_output (id, graph_node_execution_id, payload, is_current, created_at)
           SELECT id, graph_node_execution_id, state_data, is_current, created_at
           FROM graph_node_execution_state WHERE direction = 'OUTPUT'"""
    )

    op.drop_index(
        "uq_graph_node_execution_state_gnode_id_direction_current",
        table_name="graph_node_execution_state",
    )
    op.drop_index(
        "ix_graph_node_execution_state_graph_node_execution_id",
        table_name="graph_node_execution_state",
    )
    op.drop_table("graph_node_execution_state")
