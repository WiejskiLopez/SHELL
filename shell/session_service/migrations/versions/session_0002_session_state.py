"""Create the ``session_state`` table (static, from the SessionState ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "session_0002_session_state"
down_revision = "session_0001_session"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "session_state",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("direction", sa.String(), nullable=False),
        sa.Column("state_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["session.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("session_state")
