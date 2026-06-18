"""Phase 18 — add parent_task_execution_id to task_execution for hierarchical decomposition.

Revision ID: 010
Revises: 009
Create Date: 2026-06-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("task_execution") as batch:
        batch.add_column(
            sa.Column(
                "parent_task_execution_id",
                sa.String(36),
                nullable=True,
            )
        )
        batch.create_index(
            "ix_task_execution_parent_id",
            ["parent_task_execution_id"],
        )
        batch.create_foreign_key(
            "fk_task_execution_parent",
            "task_execution",
            ["parent_task_execution_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("task_execution") as batch:
        batch.drop_constraint("fk_task_execution_parent", type_="foreignkey")
        batch.drop_index("ix_task_execution_parent_id")
        batch.drop_column("parent_task_execution_id")
