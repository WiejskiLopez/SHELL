"""Create the ``scheduler_job`` table (static, from the SchedulerJob ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "scheduling_0003_scheduler_job"
down_revision = "scheduling_0002_scheduler_execution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scheduler_job",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("scheduler_definition_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("job_type", sa.String(), nullable=False),
        sa.Column("interval_seconds", sa.Float(), nullable=False),
        sa.Column("batch_size", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
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
    op.drop_table("scheduler_job")
