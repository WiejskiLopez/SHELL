"""Create the ``runner_config`` table (static, from the RunnerConfig ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "definition_0003_runner_config"
down_revision = "definition_0002_node_definition"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runner_config",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("package_name", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("hash", sa.String(length=64), nullable=False),
        sa.Column("body", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("runner_config")
