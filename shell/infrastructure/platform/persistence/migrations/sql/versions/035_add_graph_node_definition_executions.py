"""Add graph_node_definition_executions JSONB column to graph_execution.

Revision ID: 035
Revises: 034
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "035"
down_revision = "034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("graph_execution") as batch:
        batch.add_column(
            sa.Column(
                "graph_node_definition_executions", sa.JSON, nullable=False, server_default="{}"
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("graph_execution") as batch:
        batch.drop_column("graph_node_definition_executions")
