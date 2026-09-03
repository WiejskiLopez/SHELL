"""Create the ``edge_execution`` table (static, from the EdgeExecution ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "execution_0010_edge_execution"
down_revision = "execution_0009_workflow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "edge_execution",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("edge_definition_id", sa.String(), nullable=False),
        sa.Column("source_node_execution_id", sa.String(), nullable=False),
        sa.Column("target_node_execution_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["target_node_execution_id"],
            ["node_execution.id"],
            ondelete="SET NULL",
        ),
    )


def downgrade() -> None:
    op.drop_table("edge_execution")
