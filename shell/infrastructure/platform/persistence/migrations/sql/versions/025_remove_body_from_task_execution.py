"""Remove body column from task_execution — content moves to task_execution_state_input.payload.

Revision ID: 025
Revises: 024
Create Date: 2026-06-21

* Drop ``task_execution.body``
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "025"
down_revision = "024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("task_execution") as batch:
        batch.drop_column("body")


def downgrade() -> None:
    with op.batch_alter_table("task_execution") as batch:
        batch.add_column(
            sa.Column("body", sa.Text(), nullable=False, server_default="")
        )
