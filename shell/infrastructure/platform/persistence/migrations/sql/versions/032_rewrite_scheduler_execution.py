"""Rewrite scheduler_execution table — replace old execution tracking columns with SchedulerJob model.

Revision ID: 033
Revises: 032

Old columns (from v016): scheduler_definition_id, status, trigger_event_id,
  trigger_event_type, action_ref, action_ref_type, input_state, output_state,
  error, started_at, completed_at, created_at, updated_at, version
New columns (SchedulerJob model): scheduler_definition_id, name, job_type,
  interval_seconds, batch_size, enabled, config, created_at, updated_at, version

The FK to scheduler_definition (scheduler_definition_id) is preserved.
The version column (from v031) is preserved.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "032"
down_revision = "031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_se_status", table_name="scheduler_execution")
    op.drop_index("ix_se_action_ref", table_name="scheduler_execution")

    with op.batch_alter_table("scheduler_execution") as batch:
        batch.drop_column("status")
        batch.drop_column("trigger_event_id")
        batch.drop_column("trigger_event_type")
        batch.drop_column("action_ref")
        batch.drop_column("action_ref_type")
        batch.drop_column("input_state")
        batch.drop_column("output_state")
        batch.drop_column("error")
        batch.drop_column("started_at")
        batch.drop_column("completed_at")

        batch.add_column(sa.Column("name", sa.String(255), nullable=False, server_default=""))
        batch.add_column(sa.Column("job_type", sa.String(64), nullable=False, server_default="messaging"))
        batch.add_column(sa.Column("interval_seconds", sa.Float(), nullable=False, server_default="1.0"))
        batch.add_column(sa.Column("batch_size", sa.Integer(), nullable=False, server_default="50"))
        batch.add_column(sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"))
        batch.add_column(sa.Column("config", sa.JSON(), nullable=False, server_default="{}"))


def downgrade() -> None:
    with op.batch_alter_table("scheduler_execution") as batch:
        batch.drop_column("config")
        batch.drop_column("enabled")
        batch.drop_column("batch_size")
        batch.drop_column("interval_seconds")
        batch.drop_column("job_type")
        batch.drop_column("name")

        batch.add_column(sa.Column("completed_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("started_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("error", sa.Text(), nullable=True))
        batch.add_column(sa.Column("output_state", sa.JSON(), nullable=False, server_default="{}"))
        batch.add_column(sa.Column("input_state", sa.JSON(), nullable=False, server_default="{}"))
        batch.add_column(sa.Column("action_ref_type", sa.String(64), nullable=True))
        batch.add_column(sa.Column("action_ref", sa.String(255), nullable=True))
        batch.add_column(sa.Column("trigger_event_type", sa.String(128), nullable=True))
        batch.add_column(sa.Column("trigger_event_id", sa.String(255), nullable=True))
        batch.add_column(sa.Column("status", sa.String(32), nullable=False, server_default="pending"))

    op.create_index("ix_se_action_ref", "scheduler_execution", ["action_ref"])
    op.create_index("ix_se_status", "scheduler_execution", ["status"])
