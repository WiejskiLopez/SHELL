"""Add initialization_status column to graph_execution.

Revision ID: 038
Revises: 037
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "038"
down_revision = "037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("graph_execution") as batch:
        batch.add_column(
            sa.Column("initialization_status", sa.String, nullable=False, server_default="pending")
        )


def downgrade() -> None:
    with op.batch_alter_table("graph_execution") as batch:
        batch.drop_column("initialization_status")
