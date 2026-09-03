"""Create the ``agent_config_execution`` table (static, from the ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "execution_0001_agent_config_execution"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_config_execution",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("agent_execution_id", sa.String(), nullable=False),
        sa.Column("config_data", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("agent_config_execution")
