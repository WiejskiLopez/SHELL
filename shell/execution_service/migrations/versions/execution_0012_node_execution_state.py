"""Create the ``node_execution_state`` table (static, from the ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "execution_0012_node_execution_state"
down_revision = "execution_0011_graph_execution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "node_execution_state",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("node_execution_id", sa.String(), nullable=False),
        sa.Column("direction", sa.String(), nullable=False),
        sa.Column("state_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["node_execution_id"],
            ["node_execution.id"],
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    op.drop_table("node_execution_state")
