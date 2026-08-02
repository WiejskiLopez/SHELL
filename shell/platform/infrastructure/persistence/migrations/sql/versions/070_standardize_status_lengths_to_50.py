"""Standardize status column lengths.

Revision ID: 070
Revises: 069
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "070"
down_revision = "069"
branch_labels = None
depends_on = None

_STATUS_COLUMNS = (
    ("workflow", "status", sa.String(32)),
    ("graph_execution", "status", sa.String(20)),
    ("task_execution", "status", sa.String(20)),
    ("node_execution", "status", sa.String()),
    ("node_execution_result", "status", sa.String(32)),
    ("session", "status", sa.String(16)),
    ("project", "status", sa.String()),
    ("user", "status", sa.String()),
    ("scheduler_job", "status", sa.String()),
)


def upgrade() -> None:
    for table_name, column_name, existing_type in _STATUS_COLUMNS:
        with op.batch_alter_table(table_name) as batch:
            batch.alter_column(
                column_name,
                existing_type=existing_type,
                type_=sa.String(50),
            )


def downgrade() -> None:
    for table_name, column_name, existing_type in reversed(_STATUS_COLUMNS):
        with op.batch_alter_table(table_name) as batch:
            batch.alter_column(
                column_name,
                existing_type=sa.String(50),
                type_=existing_type,
            )
