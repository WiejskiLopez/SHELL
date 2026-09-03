"""Create the ``task_execution`` table (static, from the TaskExecution ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "execution_0007_task_execution"
down_revision = "execution_0006_session_execution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_execution",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("work_dir", sa.String(), nullable=False),
        sa.Column("workflow_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("task_execution")
