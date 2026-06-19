"""Phase 16 — adds task_execution_input_payload and task_execution_output_payload tables.

Revision ID: 008
Revises: 007
Create Date: 2026-06-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_execution_input_payload",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_execution_id", sa.String(36), sa.ForeignKey("task_execution.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_task_execution_input_payload_task_execution_id",
        "task_execution_input_payload",
        ["task_execution_id"],
    )
    op.create_index(
        "uq_task_execution_input_payload_is_current",
        "task_execution_input_payload",
        ["task_execution_id"],
        postgresql_where=sa.text("is_current = true"),
        sqlite_where=sa.text("is_current = 1"),
        unique=True,
    )

    op.create_table(
        "task_execution_output_payload",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_execution_id", sa.String(36), sa.ForeignKey("task_execution.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_task_execution_output_payload_task_execution_id",
        "task_execution_output_payload",
        ["task_execution_id"],
    )
    op.create_index(
        "uq_task_execution_output_payload_is_current",
        "task_execution_output_payload",
        ["task_execution_id"],
        postgresql_where=sa.text("is_current = true"),
        sqlite_where=sa.text("is_current = 1"),
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_task_execution_output_payload_is_current", table_name="task_execution_output_payload")
    op.drop_index("ix_task_execution_output_payload_task_execution_id", table_name="task_execution_output_payload")
    op.drop_table("task_execution_output_payload")
    op.drop_index("uq_task_execution_input_payload_is_current", table_name="task_execution_input_payload")
    op.drop_index("ix_task_execution_input_payload_task_execution_id", table_name="task_execution_input_payload")
    op.drop_table("task_execution_input_payload")
