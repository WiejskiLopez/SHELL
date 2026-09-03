"""Create the ``user_state`` table (static, from the UserState ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "user_0002_user_state"
down_revision = "user_0001_user"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_state",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("direction", sa.String(), nullable=False),
        sa.Column("state_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("user_state")
