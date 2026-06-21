"""Phase 13 — split Task / Graph aggregates.

Revision ID: 005
Revises: 004
Create Date: 2026-06-15

* Drop ``task_execution.graph_definition_id``
* Rename ``task_execution.task_text`` -> ``task_execution.body``
* Add ``graph_execution.graph_definition_id``
* Make ``graph_execution.task_execution_id`` UNIQUE (1:1 with TaskExecution)
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("task_execution") as batch:
        batch.drop_column("graph_definition_id")
        batch.alter_column(
            "task_text",
            new_column_name="body",
            existing_type=sa.Text(),
            existing_nullable=False,
            existing_server_default="",
        )

    with op.batch_alter_table("graph_execution") as batch:
        batch.add_column(
            sa.Column(
                "graph_definition_id",
                sa.String(36),
                nullable=False,
                server_default="",
            )
        )
        batch.drop_index("ix_graph_execution_task_execution_id")
        batch.create_index(
            "uq_graph_execution_task_execution_id", ["task_execution_id"], unique=True
        )


def downgrade() -> None:
    with op.batch_alter_table("graph_execution") as batch:
        batch.drop_index("uq_graph_execution_task_execution_id")
        batch.create_index("ix_graph_execution_task_execution_id", ["task_execution_id"])
        batch.drop_column("graph_definition_id")

    with op.batch_alter_table("task_execution") as batch:
        batch.alter_column(
            "body",
            new_column_name="task_text",
            existing_type=sa.Text(),
            existing_nullable=False,
            existing_server_default="",
        )
        batch.add_column(
            sa.Column(
                "graph_definition_id",
                sa.String(36),
                nullable=False,
                server_default="",
            )
        )
