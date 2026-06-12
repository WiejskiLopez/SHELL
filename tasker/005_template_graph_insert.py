"""Faza 12 — adds outbox_event table.

Revision ID: 004
Revises: 003
Create Date: 2026-06-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:

    template_graph_table = op.create_table(
        "template_graph",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(36), nullable=False),
        sa.Column("purpose", sa.String(36), nullable=False),
    )

    op.bulk_insert(
        template_graph_table,
        [
            {
                "id": "base-planner-id",
                "name": "base_planner",
                "purpose": "system_default_planner"
            }
        ]
    )

    op.create_table(
        "template_graph_node",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("template_graph_id", sa.String(36), sa.ForeignKey("template_graph.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("role", sa.String(128), nullable=False),
        sa.Column("node_type", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("command", sa.Text, nullable=False),
        sa.Column("timeout", sa.Integer, nullable=False),
        sa.Column("retries", sa.Integer, nullable=False),
        sa.Column("log_level", sa.String(16), nullable=False),
        sa.Column("max_step", sa.Integer, nullable=True),
        sa.Column("no_ask_user", sa.Boolean, nullable=True),
        sa.Column("autopilot", sa.Boolean, nullable=True),
        sa.Column("status_initial", sa.String(64), nullable=False),
        sa.Column("extra", sa.JSON, nullable=True),
        sa.Column("script", sa.Text, nullable=True),
        sa.Column("script_type", sa.String(16), nullable=True),
    )
    op.create_index("ix_template_graph_node_graph_id", "template_graph_node", ["template_graph_id"])


def downgrade() -> None:
    op.drop_index("ix_template_graph_node_graph_id", table_name="template_graph_node")
    op.drop_table("template_graph_node")
    op.drop_table("template_graph")
