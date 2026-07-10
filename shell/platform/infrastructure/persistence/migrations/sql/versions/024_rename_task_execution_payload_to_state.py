"""Phase rename — rename task_execution_*_payload tables to task_execution_state_*.

Revision ID: 024
Revises: 023
Create Date: 2026-06-21

* Rename ``task_execution_input_payload`` → ``task_execution_state_input``
* Rename ``task_execution_output_payload`` → ``task_execution_state_output``
"""

from __future__ import annotations

from alembic import op

revision = "024"
down_revision = "023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("task_execution_input_payload", "task_execution_state_input")
    op.rename_table("task_execution_output_payload", "task_execution_state_output")


def downgrade() -> None:
    op.rename_table("task_execution_state_output", "task_execution_output_payload")
    op.rename_table("task_execution_state_input", "task_execution_input_payload")
