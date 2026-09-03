"""Create the ``user_execution`` table (static, from the UserExecution ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "execution_0008_user_execution"
down_revision = "execution_0007_task_execution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_execution",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("user_execution")
