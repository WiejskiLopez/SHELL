"""Drop body column from task_execution.

Revision ID: 060
Revises: 059
Create Date: 2026-07-19

* Drop ``task_execution.body`` (Text, nullable=False)
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "060"
down_revision = "059"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("task_execution") as batch:
        batch.drop_column("body")


def downgrade() -> None:
    with op.batch_alter_table("task_execution") as batch:
        batch.add_column(sa.Column("body", sa.Text(), nullable=False, server_default=""))
