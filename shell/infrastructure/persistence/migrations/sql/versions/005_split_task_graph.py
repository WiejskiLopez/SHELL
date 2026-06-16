"""Phase 13 — split Task / Graph aggregates.

Revision ID: 005
Revises: 004
Create Date: 2026-06-15

* Drop ``task.template_graph_id``
* Rename ``task.task_text`` -> ``task.body``
* Add ``graph.template_graph_id``
* Make ``graph.task_id`` UNIQUE (1:1 with Task)
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("task") as batch:
        batch.drop_column("template_graph_id")
        batch.alter_column(
            "task_text",
            new_column_name="body",
            existing_type=sa.Text(),
            existing_nullable=False,
            existing_server_default="",
        )

    with op.batch_alter_table("graph") as batch:
        batch.add_column(
            sa.Column(
                "template_graph_id",
                sa.String(36),
                nullable=False,
                server_default="",
            )
        )
        batch.create_unique_constraint("uq_graph_task_id", ["task_id"])


def downgrade() -> None:
    with op.batch_alter_table("graph") as batch:
        batch.drop_constraint("uq_graph_task_id", type_="unique")
        batch.drop_column("template_graph_id")

    with op.batch_alter_table("task") as batch:
        batch.alter_column(
            "body",
            new_column_name="task_text",
            existing_type=sa.Text(),
            existing_nullable=False,
            existing_server_default="",
        )
        batch.add_column(
            sa.Column(
                "template_graph_id",
                sa.String(36),
                nullable=False,
                server_default="",
            )
        )
