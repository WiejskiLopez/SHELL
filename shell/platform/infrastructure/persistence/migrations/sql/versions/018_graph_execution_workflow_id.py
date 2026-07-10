"""Phase fix — add workflow_id column to graph_execution table.

Revision ID: 018
Revises: 017
Create Date: 2026-06-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("graph_execution") as batch:
        batch.add_column(sa.Column("workflow_id", sa.String(36), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("graph_execution") as batch:
        batch.drop_column("workflow_id")
