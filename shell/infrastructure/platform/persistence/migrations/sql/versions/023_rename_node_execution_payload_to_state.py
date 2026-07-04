"""Phase rename — rename node_execution_*_payload tables to node_execution_state_*.

Revision ID: 023
Revises: 022
Create Date: 2026-06-21

* Rename ``node_execution_input_payload`` → ``node_execution_state_input``
* Rename ``node_execution_output_payload`` → ``node_execution_state_output``
"""

from __future__ import annotations

from alembic import op

revision = "023"
down_revision = "022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("node_execution_input_payload", "node_execution_state_input")
    op.rename_table("node_execution_output_payload", "node_execution_state_output")


def downgrade() -> None:
    op.rename_table("node_execution_state_output", "node_execution_output_payload")
    op.rename_table("node_execution_state_input", "node_execution_input_payload")
