"""Add version column for optimistic locking.

Revision ID: 031
Revises: 030
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "031"
down_revision = "030"
branch_labels = None
depends_on = None

TABLES = [
    "workflow",
    "task_execution",
    "graph_execution",
    "node_execution",
    "node_transition_execution",
    "session",
    "envelope",
    "graph_definition",
    "node_definition",
    "runner_config",
    "rag_document",
    "scheduler_execution",
    "scheduler_definition",
]


def upgrade() -> None:
    for table in TABLES:
        with op.batch_alter_table(table) as batch:
            batch.add_column(
                sa.Column(
                    "version",
                    sa.Integer(),
                    nullable=False,
                    server_default="1",
                ),
            )


def downgrade() -> None:
    for table in TABLES:
        with op.batch_alter_table(table) as batch:
            batch.drop_column("version")
