"""Create edge_link_execution table.

Revision ID: 052
Revises: 051
Create Date: 2026-07-05

Changes:
* Create ``edge_link_execution`` table with columns: id, node_execution_id,
  edge_execution_id, created_at, updated_at, deleted_at, version
* Add indexes on node_execution_id and edge_execution_id
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "052"
down_revision = "051"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "edge_link_execution",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("node_execution_id", sa.String(), nullable=False),
        sa.Column("edge_execution_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(
            ["node_execution_id"],
            ["node_execution.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["edge_execution_id"],
            ["edge_execution.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_edge_link_execution_node_execution_id",
        "edge_link_execution",
        ["node_execution_id"],
    )
    op.create_index(
        "ix_edge_link_execution_edge_execution_id",
        "edge_link_execution",
        ["edge_execution_id"],
    )

    op.add_column("session", sa.Column("closed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("session", "closed_at")
    op.drop_index("ix_edge_link_execution_edge_execution_id", table_name="edge_link_execution")
    op.drop_index("ix_edge_link_execution_node_execution_id", table_name="edge_link_execution")
    op.drop_table("edge_link_execution")
