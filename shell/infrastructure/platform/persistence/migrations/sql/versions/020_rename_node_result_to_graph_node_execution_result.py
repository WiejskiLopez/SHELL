"""Phase fix — rename node_result to graph_node_execution_result.

Revision ID: 020
Revises: 019
Create Date: 2026-06-20

Drop the legacy ``node_result`` table and create ``graph_node_execution_result``
with the column names matching the ORM model.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("node_result")

    op.create_table(
        "graph_node_execution_result",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("graph_node_execution_id", sa.String(255), nullable=False),
        sa.Column("workflow_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("stdout", sa.Text, nullable=False, server_default=""),
        sa.Column("stderr", sa.Text, nullable=False, server_default=""),
        sa.Column("artifact_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_graph_node_execution_result_node_execution_id",
        "graph_node_execution_result",
        ["graph_node_execution_id"],
    )
    op.create_index(
        "ix_graph_node_execution_result_workflow_id",
        "graph_node_execution_result",
        ["workflow_id"],
    )


def downgrade() -> None:
    op.drop_table("graph_node_execution_result")

    op.create_table(
        "node_result",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("node_execution_id", sa.String(255), nullable=False),
        sa.Column("workflow_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("stdout", sa.Text, nullable=False, server_default=""),
        sa.Column("stderr", sa.Text, nullable=False, server_default=""),
        sa.Column("artifact_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_node_result_node_execution_id", "node_result", ["node_execution_id"])
    op.create_index("ix_node_result_workflow_id", "node_result", ["workflow_id"])
