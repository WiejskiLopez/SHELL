"""Create node_link_definition and node_link_execution tables.

Revision ID: 047
Revises: 046
Create Date: 2026-07-02

* Create ``node_link_definition`` table
* Create ``node_link_execution`` table
* Seed initial link data from existing graph_definition ↔ node_definition
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "047"
down_revision = "046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === node_link_definition ===
    op.create_table(
        "node_link_definition",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "graph_definition_id",
            sa.String(),
            sa.ForeignKey("graph_definition.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "node_definition_id",
            sa.String(),
            sa.ForeignKey("node_definition.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_node_link_definition_graph_definition_id",
        "node_link_definition",
        ["graph_definition_id"],
    )
    op.create_index(
        "ix_node_link_definition_node_definition_id",
        "node_link_definition",
        ["node_definition_id"],
    )

    # === node_link_execution ===
    op.create_table(
        "node_link_execution",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "graph_execution_id",
            sa.String(),
            sa.ForeignKey("graph_execution.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "node_execution_id",
            sa.String(),
            sa.ForeignKey("node_execution.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_node_link_execution_graph_execution_id",
        "node_link_execution",
        ["graph_execution_id"],
    )
    op.create_index(
        "ix_node_link_execution_node_execution_id",
        "node_link_execution",
        ["node_execution_id"],
    )

    # === Seed data: create links for existing definitions ===
    conn = op.get_bind()

    rows = conn.execute(
        sa.text(
            "SELECT id, graph_definition_id FROM node_definition "
            "WHERE graph_definition_id IS NOT NULL AND graph_definition_id != ''"
        )
    ).fetchall()

    for node_def_id, graph_def_id in rows:
        link_id = f"gndl-{graph_def_id}-{node_def_id}"
        conn.execute(
            sa.text(
                "INSERT OR IGNORE INTO node_link_definition "
                "(id, graph_definition_id, node_definition_id, version) "
                "VALUES (:id, :gdef_id, :ndef_id, 1)"
            ),
            {"id": link_id, "gdef_id": graph_def_id, "ndef_id": node_def_id},
        )


def downgrade() -> None:
    op.drop_table("node_link_execution")
    op.drop_table("node_link_definition")
