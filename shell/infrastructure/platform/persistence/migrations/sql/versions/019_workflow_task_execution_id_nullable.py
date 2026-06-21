"""Phase fix — make workflow.task_execution_id nullable.

Revision ID: 019
Revises: 018
Create Date: 2026-06-20

The ORM model no longer maps task_execution_id; make the column nullable
so new Workflow records can be persisted without it.
"""

from __future__ import annotations

from alembic import op

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("workflow") as batch:
        batch.alter_column("task_execution_id", nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("workflow") as batch:
        batch.alter_column("task_execution_id", nullable=False)
