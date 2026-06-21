"""Phase 20 — move work_dir from workflow to task_execution, remove node_dir from graph_node_execution.

Revision ID: 012
Revises: 011
Create Date: 2026-06-19

* Add ``task_execution.work_dir`` — execution context moved from workflow.
* Remove ``workflow.work_dir`` — no longer needed (comes from task_execution).
* Remove ``graph_node_execution.node_dir`` — redundant (never used in production).
* Remove ``graph_node_execution.work_dir`` — redundant (comes from task_execution).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- task_execution: add work_dir ---
    with op.batch_alter_table("task_execution") as batch:
        batch.add_column(sa.Column("work_dir", sa.String(512), nullable=False, server_default=""))

    # --- workflow: drop work_dir ---
    with op.batch_alter_table("workflow") as batch:
        batch.drop_column("work_dir")

    # --- graph_node_execution: drop node_dir and work_dir ---
    with op.batch_alter_table("graph_node_execution") as batch:
        batch.drop_column("node_dir")
        batch.drop_column("work_dir")


def downgrade() -> None:
    with op.batch_alter_table("graph_node_execution") as batch:
        batch.add_column(sa.Column("work_dir", sa.String(512), nullable=False, server_default=""))
        batch.add_column(sa.Column("node_dir", sa.String(512), nullable=False, server_default=""))

    with op.batch_alter_table("workflow") as batch:
        batch.add_column(sa.Column("work_dir", sa.String(1024), nullable=False, server_default=""))

    with op.batch_alter_table("task_execution") as batch:
        batch.drop_column("work_dir")
