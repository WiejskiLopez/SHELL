"""Create the ``user_skill`` table (static, from the UserSkill ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "user_0003_user_skill"
down_revision = "user_0002_user_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_skill",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("skill_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("user_skill")
