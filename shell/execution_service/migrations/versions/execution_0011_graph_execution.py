"""Create the ``graph_execution`` table (static, from the GraphExecution ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "execution_0011_graph_execution"
down_revision = "execution_0010_edge_execution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "graph_execution",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("task_execution_id", sa.String(), nullable=False),
        sa.Column("graph_definition_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("parent_graph_execution_id", sa.String(), nullable=True),
        sa.Column("state_input", sa.JSON(), nullable=False),
        sa.Column("state_output", sa.JSON(), nullable=False),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.Column("max_subgraph_depth", sa.Integer(), nullable=False),
        sa.Column("timeout_at", sa.DateTime(), nullable=True),
        sa.Column("correlation_id", sa.String(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_execution_id"],
            ["task_execution.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_graph_execution_id"],
            ["graph_execution.id"],
            ondelete="SET NULL",
        ),
    )


def downgrade() -> None:
    op.drop_table("graph_execution")
