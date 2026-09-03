"""Create the ``node_execution`` table (static, from the NodeExecution ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "execution_0004_node_execution"
down_revision = "execution_0003_agent_skill_execution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "node_execution",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("node_type", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("command", sa.String(), nullable=False),
        sa.Column("retries", sa.Integer(), nullable=False),
        sa.Column("log_level", sa.String(), nullable=False),
        sa.Column("max_step", sa.Integer(), nullable=False),
        sa.Column("no_ask_user", sa.Boolean(), nullable=False),
        sa.Column("autopilot", sa.Boolean(), nullable=False),
        sa.Column("task_execution_id", sa.String(), nullable=False),
        sa.Column("source_dir", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("status_initial", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("node_execution")
