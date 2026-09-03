"""Create the ``scheduler_execution`` table (static, from the ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "scheduling_0002_scheduler_execution"
down_revision = "scheduling_0001_scheduler_definition"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scheduler_execution",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("scheduler_definition_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("trigger_event_id", sa.String(), nullable=True),
        sa.Column("trigger_event_type", sa.String(), nullable=True),
        sa.Column("action_ref", sa.String(), nullable=True),
        sa.Column("action_ref_type", sa.String(), nullable=True),
        sa.Column("input_state", sa.JSON(), nullable=True),
        sa.Column("output_state", sa.JSON(), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["scheduler_definition_id"],
            ["scheduler_definition.id"],
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    op.drop_table("scheduler_execution")
