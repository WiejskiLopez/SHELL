"""Add status column to graph_node_execution.

Revision ID: 036
Revises: 035
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "036"
down_revision = "035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("graph_node_execution") as batch:
        batch.add_column(sa.Column("status", sa.String, nullable=False, server_default="pending"))


def downgrade() -> None:
    with op.batch_alter_table("graph_node_execution") as batch:
        batch.drop_column("status")
