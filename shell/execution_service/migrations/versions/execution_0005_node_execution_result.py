"""Create the ``node_execution_result`` table (static, from the ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "execution_0005_node_execution_result"
down_revision = "execution_0004_node_execution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "node_execution_result",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("node_execution_id", sa.String(), nullable=False),
        sa.Column("workflow_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("stdout", sa.String(), nullable=False),
        sa.Column("stderr", sa.String(), nullable=False),
        sa.Column("artifact_uri", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("node_execution_result")
