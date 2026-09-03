"""Create the ``node_link_execution`` table (static, from the NodeLinkExecution ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "execution_0019_node_link_execution"
down_revision = "execution_0018_graph_execution_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "node_link_execution",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("graph_execution_id", sa.String(), nullable=False),
        sa.Column("node_execution_id", sa.String(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["graph_execution_id"],
            ["graph_execution.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["node_execution_id"],
            ["node_execution.id"],
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    op.drop_table("node_link_execution")
