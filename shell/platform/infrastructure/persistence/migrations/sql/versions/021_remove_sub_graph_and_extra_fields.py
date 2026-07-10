"""Phase cleanup — remove sub-graph and extra fields that are no longer used.

Revision ID: 021
Revises: 020
Create Date: 2026-06-21

* Drop ``sub_graph_definition_id``, ``sub_graph_definition_version``, ``extra``
  from ``node_execution``.
* Drop ``extra`` from ``node_definition``.
* Drop ``parent_tasker_node_execution_id`` from ``graph_execution``
  (was already removed from ORM/domain; only lingered in Alembic 015).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── node_execution ───────────────────────────────────────────────
    with op.batch_alter_table("node_execution") as batch:
        batch.drop_column("sub_graph_definition_id")
        batch.drop_column("sub_graph_definition_version")
        batch.drop_column("extra")

    # ── node_definition ──────────────────────────────────────────────
    with op.batch_alter_table("node_definition") as batch:
        batch.drop_column("extra")

    # ── graph_execution ────────────────────────────────────────────────────
    with op.batch_alter_table("graph_execution") as batch:
        batch.drop_index("ix_graph_execution_parent_tasker_node_execution_id")
        batch.drop_column("parent_tasker_node_execution_id")


def downgrade() -> None:
    # ── graph_execution ────────────────────────────────────────────────────
    with op.batch_alter_table("graph_execution") as batch:
        batch.add_column(
            sa.Column("parent_tasker_node_execution_id", sa.String(36), nullable=True),
        )
        batch.create_index(
            "ix_graph_execution_parent_tasker_node_execution_id",
            ["parent_tasker_node_execution_id"],
        )

    # ── node_definition ──────────────────────────────────────────────
    with op.batch_alter_table("node_definition") as batch:
        batch.add_column(
            sa.Column("extra", sa.JSON, nullable=True),
        )

    # ── node_execution ───────────────────────────────────────────────
    with op.batch_alter_table("node_execution") as batch:
        batch.add_column(
            sa.Column("extra", sa.JSON, nullable=False, server_default="{}"),
        )
        batch.add_column(
            sa.Column("sub_graph_definition_version", sa.Integer, nullable=True),
        )
        batch.add_column(
            sa.Column("sub_graph_definition_id", sa.String(36), nullable=True),
        )
