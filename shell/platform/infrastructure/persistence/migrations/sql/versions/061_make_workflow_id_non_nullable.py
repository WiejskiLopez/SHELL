"""Make workflow_id non-nullable in task_execution.

Revision ID: 061
Revises: 060
Create Date: 2026-07-19

* Change ``task_execution.workflow_id`` from nullable to non-nullable
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "061"
down_revision = "060"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("task_execution") as batch:
        batch.alter_column("workflow_id", existing_type=sa.String(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("task_execution") as batch:
        batch.alter_column("workflow_id", existing_type=sa.String(), nullable=True)
