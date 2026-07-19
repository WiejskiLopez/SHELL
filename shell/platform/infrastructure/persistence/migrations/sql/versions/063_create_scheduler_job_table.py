"""Create scheduler_job table for SchedulerExecution (one-shot) records.

Revision ID: 063
Revises: 062
Create Date: 2026-07-19

This table was referenced in migration 050 but never created.
It stores one-shot evaluation records (SchedulerExecution domain aggregate),
while scheduler_execution table stores cyclic job config (SchedulerJob).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "063"
down_revision = "062"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scheduler_job",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("scheduler_execution_id", sa.String(), nullable=True),
        sa.Column("scheduler_definition_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
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
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(
            ["scheduler_execution_id"],
            ["scheduler_execution.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["scheduler_definition_id"],
            ["scheduler_definition.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_scheduler_job_status",
        "scheduler_job",
        ["status"],
    )
    op.create_index(
        "ix_scheduler_job_definition_id",
        "scheduler_job",
        ["scheduler_definition_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_scheduler_job_status", table_name="scheduler_job")
    op.drop_index("ix_scheduler_job_definition_id", table_name="scheduler_job")
    op.drop_table("scheduler_job")
