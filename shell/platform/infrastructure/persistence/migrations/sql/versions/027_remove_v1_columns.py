"""Remove V1 columns from workflow and task_execution — cursor, version, is_current, parent_task_execution_id.

Revision ID: 027
Revises: 026
Create Date: 2026-06-22

* Drop ``workflow.current_node_execution_id`` — V1 cursor (removed in V2)
* Drop ``workflow.version`` — V1 optimistic locking (removed in V2)
* Drop ``workflow.task_execution_id`` — V1 FK to task_execution (removed in V2)
* Drop ``task_execution.version`` — V1 optimistic locking (removed in V2)
* Drop ``task_execution.is_current`` — V1 flag (removed in V2)
* Drop ``task_execution.parent_task_execution_id`` — V1 hierarchical decomposition (removed in V2)
* Kept ``workflow.correlation_id`` — still used for tracing
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "027"
down_revision = "026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("workflow") as batch:
        batch.drop_index("ix_workflow_current_node_execution_id")
        batch.drop_index("ix_workflow_task_execution_id")
        batch.drop_column("current_node_execution_id")
        batch.drop_column("version")
        batch.drop_column("task_execution_id")

    with op.batch_alter_table("task_execution") as batch:
        batch.drop_index("ix_task_execution_parent_task_execution_id")
        batch.drop_column("version")
        batch.drop_column("is_current")
        batch.drop_column("parent_task_execution_id")


def downgrade() -> None:
    with op.batch_alter_table("task_execution") as batch:
        batch.add_column(sa.Column("parent_task_execution_id", sa.String(36), nullable=True))
        batch.add_column(
            sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true"))
        )
        batch.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
        batch.create_index(
            "ix_task_execution_parent_task_execution_id", ["parent_task_execution_id"]
        )

    with op.batch_alter_table("workflow") as batch:
        batch.add_column(sa.Column("task_execution_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
        batch.add_column(sa.Column("current_node_execution_id", sa.String(255), nullable=True))
        batch.create_index("ix_workflow_task_execution_id", ["task_execution_id"])
        batch.create_index("ix_workflow_current_node_execution_id", ["current_node_execution_id"])
