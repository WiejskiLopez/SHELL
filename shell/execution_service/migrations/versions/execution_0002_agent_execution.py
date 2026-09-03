"""Create the ``agent_execution`` table (static, from the AgentExecution ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "execution_0002_agent_execution"
down_revision = "execution_0001_agent_config_execution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_execution",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("node_execution_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("agent_execution")
