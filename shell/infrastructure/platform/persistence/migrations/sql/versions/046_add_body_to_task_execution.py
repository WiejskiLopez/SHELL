"""Add body column to task_execution — stores task definition content.

Revision ID: 046
Revises: 045
Create Date: 2026-06-30

* Add ``task_execution.body`` (Text, nullable=False, default="")
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "046"
down_revision = "045"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "task_execution",
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("task_execution", "body")
