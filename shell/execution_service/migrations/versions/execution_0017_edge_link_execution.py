"""Create the ``edge_link_execution`` table (static, from the ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "execution_0017_edge_link_execution"
down_revision = "execution_0016_workflow_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "edge_link_execution",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("node_execution_id", sa.String(), nullable=False),
        sa.Column("edge_execution_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
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
    )


def downgrade() -> None:
    op.drop_table("edge_link_execution")
