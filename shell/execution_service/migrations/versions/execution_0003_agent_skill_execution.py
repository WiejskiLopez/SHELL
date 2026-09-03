"""Create the ``agent_skill_execution`` table (static, from the ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "execution_0003_agent_skill_execution"
down_revision = "execution_0002_agent_execution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_skill_execution",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("agent_execution_id", sa.String(), nullable=False),
        sa.Column("skill_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("agent_skill_execution")
