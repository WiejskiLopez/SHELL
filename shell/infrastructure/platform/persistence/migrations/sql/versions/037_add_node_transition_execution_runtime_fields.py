"""Add current_iteration and status columns to node_transition_execution.

Revision ID: 037
Revises: 036
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "037"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("node_transition_execution") as batch:
        batch.add_column(
            sa.Column("current_iteration", sa.Integer, nullable=False, server_default="0")
        )
        batch.add_column(sa.Column("status", sa.String, nullable=False, server_default="evaluated"))


def downgrade() -> None:
    with op.batch_alter_table("node_transition_execution") as batch:
        batch.drop_column("current_iteration")
        batch.drop_column("status")
