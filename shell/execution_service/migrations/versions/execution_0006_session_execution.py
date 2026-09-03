"""Create the ``session_execution`` table (static, from the SessionExecution ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "execution_0006_session_execution"
down_revision = "execution_0005_node_execution_result"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "session_execution",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_execution_id", sa.String(), nullable=True),
        sa.Column("session_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("session_execution")
