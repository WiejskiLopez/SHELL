"""Create the ``scheduler_definition`` table (static, from the ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "scheduling_0001_scheduler_definition"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scheduler_definition",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("source_context", sa.String(), nullable=False),
        sa.Column("trigger_event_type", sa.String(), nullable=False),
        sa.Column("trigger_filter", sa.JSON(), nullable=True),
        sa.Column("action_type", sa.String(), nullable=False),
        sa.Column("action_config", sa.JSON(), nullable=False),
        sa.Column("execution_policy", sa.JSON(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("scheduler_definition")
