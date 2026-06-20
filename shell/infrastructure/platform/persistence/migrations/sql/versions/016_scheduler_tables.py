"""Phase 24 — add scheduler_definition and scheduler_execution tables.

Revision ID: 016
Revises: 015
Create Date: 2026-06-20

* Create ``scheduler_definition`` table — defines event-triggered actions.
* Create ``scheduler_execution`` table — execution instances of definitions.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── scheduler_definition ────────────────────────────────────────────────
    op.create_table(
        "scheduler_definition",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_context", sa.String(64), nullable=False),
        sa.Column("trigger_event_type", sa.String(128), nullable=False),
        sa.Column("trigger_filter", sa.JSON(), nullable=True),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("action_config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "execution_policy", sa.JSON(), nullable=True
        ),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_sd_source_trigger",
        "scheduler_definition",
        ["source_context", "trigger_event_type"],
    )

    # ── scheduler_execution ────────────────────────────────────────────────
    op.create_table(
        "scheduler_execution",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scheduler_definition_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("trigger_event_id", sa.String(255), nullable=True),
        sa.Column("trigger_event_type", sa.String(128), nullable=True),
        sa.Column("action_ref", sa.String(255), nullable=True),
        sa.Column("action_ref_type", sa.String(64), nullable=True),
        sa.Column("input_state", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("output_state", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_se_status",
        "scheduler_execution",
        ["status"],
    )
    op.create_index(
        "ix_se_definition_id",
        "scheduler_execution",
        ["scheduler_definition_id"],
    )
    op.create_index(
        "ix_se_action_ref",
        "scheduler_execution",
        ["action_ref"],
    )


def downgrade() -> None:
    op.drop_table("scheduler_execution")
    op.drop_table("scheduler_definition")
