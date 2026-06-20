"""Phase fix — add workflow_id column to task_execution table.

Revision ID: 017
Revises: 016
Create Date: 2026-06-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("task_execution") as batch:
        batch.add_column(sa.Column("workflow_id", sa.String(36), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("task_execution") as batch:
        batch.drop_column("workflow_id")
