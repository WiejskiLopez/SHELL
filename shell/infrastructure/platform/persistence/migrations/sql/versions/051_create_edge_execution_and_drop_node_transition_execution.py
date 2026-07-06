"""Create edge_execution table, migrate data, drop node_transition_execution.

Revision ID: 051
Revises: 050
Create Date: 2026-07-05

Changes:
* Create ``edge_execution`` table with columns: id, edge_definition_id,
  source_node_execution_id, target_node_execution_id, created_at,
  updated_at, deleted_at, version
* Migrate data from ``node_transition_execution`` (id, source_node_execution_id,
  target_node_execution_id, created_at, updated_at, version)
* Drop ``node_transition_execution`` table
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "051"
down_revision = "050"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Create edge_execution table ──────────────────────────────────────
    op.create_table(
        "edge_execution",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("edge_definition_id", sa.String(), nullable=False, server_default=""),
        sa.Column("source_node_execution_id", sa.String(), nullable=False),
        sa.Column("target_node_execution_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(
            ["target_node_execution_id"],
            ["node_execution.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── 2. Migrate data from node_transition_execution ──────────────────────
    op.execute(
        """
        INSERT INTO edge_execution (
            id,
            edge_definition_id,
            source_node_execution_id,
            target_node_execution_id,
            created_at,
            updated_at,
            deleted_at,
            version
        )
        SELECT
            id,
            '' AS edge_definition_id,
            COALESCE(source_node_execution_id, '') AS source_node_execution_id,
            target_node_execution_id,
            created_at,
            updated_at,
            NULL AS deleted_at,
            COALESCE(version, 1) AS version
        FROM node_transition_execution
        """
    )

    # ── 3. Drop node_transition_execution table ─────────────────────────────
    op.drop_table("node_transition_execution")


def downgrade() -> None:
    # ── Reverse: recreate node_transition_execution ─────────────────────────
    op.create_table(
        "node_transition_execution",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("graph_execution_id", sa.String(), nullable=False),
        sa.Column("source_node_execution_id", sa.String(), nullable=True),
        sa.Column("target_node_execution_id", sa.String(), nullable=False),
        sa.Column("transition_type", sa.String(), nullable=False, server_default="sequence"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("condition_expression", sa.String(), nullable=True),
        sa.Column("condition_language", sa.String(), nullable=True),
        sa.Column("join_wait_count", sa.Integer(), nullable=True),
        sa.Column("current_iteration", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="evaluated"),
        sa.Column("max_loop_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("timeout_seconds", sa.Integer(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retry_delay_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("data_mapping", sa.JSON(), nullable=True),
        sa.Column("label", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["graph_execution_id"], ["graph_execution.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_node_execution_id"], ["node_execution.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["target_node_execution_id"], ["node_execution.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Migrate data back
    op.execute(
        """
        INSERT INTO node_transition_execution (
            id,
            graph_execution_id,
            source_node_execution_id,
            target_node_execution_id,
            transition_type,
            priority,
            condition_expression,
            condition_language,
            join_wait_count,
            current_iteration,
            status,
            max_loop_count,
            timeout_seconds,
            retry_count,
            retry_delay_seconds,
            data_mapping,
            label,
            created_at,
            updated_at,
            deleted_at,
            version
        )
        SELECT
            id,
            '' AS graph_execution_id,
            NULLIF(source_node_execution_id, ''),
            COALESCE(target_node_execution_id, ''),
            'sequence',
            0,
            NULL,
            NULL,
            NULL,
            0,
            'evaluated',
            0,
            NULL,
            0,
            0,
            '{}'::json,
            '',
            created_at,
            updated_at,
            deleted_at,
            version
        FROM edge_execution
        """
    )

    # Drop edge_execution table
    op.drop_table("edge_execution")
