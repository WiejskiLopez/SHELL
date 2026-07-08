"""Create agent_execution, agent_config_execution, agent_skill_execution, session_state tables.

Revision ID: 056
Revises: 055
Create Date: 2026-07-13

* Create ``agent_execution`` table
* Create ``agent_config_execution`` table
* Create ``agent_skill_execution`` table
* Create ``session_state`` table
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "056"
down_revision = "055"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── agent_execution ────────────────────────────────────────────────────────
    op.create_table(
        "agent_execution",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("node_execution_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── agent_config_execution ─────────────────────────────────────────────────
    op.create_table(
        "agent_config_execution",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("agent_execution_id", sa.String(), nullable=False),
        sa.Column("session_execution_id", sa.String(), nullable=True),
        sa.Column("user_execution_id", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=False, server_default=""),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("top_p", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── agent_skill_execution ──────────────────────────────────────────────────
    op.create_table(
        "agent_skill_execution",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("agent_execution_id", sa.String(), nullable=False),
        sa.Column("skill_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── session_state ──────────────────────────────────────────────────────────
    op.create_table(
        "session_state",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("direction", sa.String(), nullable=False),
        sa.Column("state_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["session.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("session_state")
    op.drop_table("agent_skill_execution")
    op.drop_table("agent_config_execution")
    op.drop_table("agent_execution")
