"""Consolidate task_execution_state_input/_output into task_execution_state,
create workflow_state table.

* Create ``task_execution_state`` table (consolidated with ``kind`` discriminator)
* Create ``workflow_state`` table
* Migrate data from ``task_execution_state_input`` to ``task_execution_state`` (kind=INPUT)
* Migrate data from ``task_execution_state_output`` to ``task_execution_state`` (kind=OUTPUT)
* Drop old ``task_execution_state_input`` and ``task_execution_state_output`` tables

Revision ID: 034
Revises: 033
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "034"
down_revision = "033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- 1. Create consolidated task_execution_state table -------------------
    op.create_table(
        "task_execution_state",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "task_execution_id",
            sa.String(36),
            sa.ForeignKey("task_execution.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("state_data", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_task_execution_state_task_execution_id",
        "task_execution_state",
        ["task_execution_id"],
    )
    op.create_index(
        "uq_task_execution_state_task_id_direction_current",
        "task_execution_state",
        ["task_execution_id", "direction"],
        postgresql_where=sa.text("is_current = true"),
        sqlite_where=sa.text("is_current = 1"),
        unique=True,
    )

    # -- 2. Migrate data from old input table --------------------------------
    op.execute(
        """INSERT INTO task_execution_state (id, task_execution_id, direction, state_data, is_current, created_at)
           SELECT id, task_execution_id, 'INPUT', payload, is_current, created_at
           FROM task_execution_state_input"""
    )

    # -- 3. Migrate data from old output table -------------------------------
    op.execute(
        """INSERT INTO task_execution_state (id, task_execution_id, direction, state_data, is_current, created_at)
           SELECT id, task_execution_id, 'OUTPUT', payload, is_current, created_at
           FROM task_execution_state_output"""
    )

    # -- 4. Drop old tables --------------------------------------------------
    op.drop_table("task_execution_state_output")
    op.drop_table("task_execution_state_input")

    # -- 5. Create workflow_state table --------------------------------------
    op.create_table(
        "workflow_state",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "workflow_id",
            sa.String(36),
            sa.ForeignKey("workflow.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("state_data", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_workflow_state_workflow_id",
        "workflow_state",
        ["workflow_id"],
    )


def downgrade() -> None:
    # -- Reverse: drop workflow_state, recreate old tables, restore data -----
    op.drop_index("ix_workflow_state_workflow_id", table_name="workflow_state")
    op.drop_table("workflow_state")

    op.create_table(
        "task_execution_state_input",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "task_execution_id",
            sa.String(36),
            sa.ForeignKey("task_execution.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "task_execution_state_output",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "task_execution_id",
            sa.String(36),
            sa.ForeignKey("task_execution.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.execute(
        """INSERT INTO task_execution_state_input (id, task_execution_id, payload, is_current, created_at)
           SELECT id, task_execution_id, state_data, is_current, created_at
           FROM task_execution_state WHERE direction = 'INPUT'"""
    )
    op.execute(
        """INSERT INTO task_execution_state_output (id, task_execution_id, payload, is_current, created_at)
           SELECT id, task_execution_id, state_data, is_current, created_at
           FROM task_execution_state WHERE direction = 'OUTPUT'"""
    )

    op.drop_index(
        "uq_task_execution_state_task_id_direction_current", table_name="task_execution_state"
    )
    op.drop_index(
        "ix_task_execution_state_task_execution_id", table_name="task_execution_state"
    )
    op.drop_table("task_execution_state")
