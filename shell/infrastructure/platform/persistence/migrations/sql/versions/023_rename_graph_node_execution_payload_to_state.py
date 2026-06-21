"""Phase rename — rename graph_node_execution_*_payload tables to graph_node_execution_state_*.

Revision ID: 023
Revises: 022
Create Date: 2026-06-21

* Rename ``graph_node_execution_input_payload`` → ``graph_node_execution_state_input``
* Rename ``graph_node_execution_output_payload`` → ``graph_node_execution_state_output``
"""

from __future__ import annotations

from alembic import op

revision = "023"
down_revision = "022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("graph_node_execution_input_payload", "graph_node_execution_state_input")
    op.rename_table("graph_node_execution_output_payload", "graph_node_execution_state_output")


def downgrade() -> None:
    op.rename_table("graph_node_execution_state_output", "graph_node_execution_output_payload")
    op.rename_table("graph_node_execution_state_input", "graph_node_execution_input_payload")
