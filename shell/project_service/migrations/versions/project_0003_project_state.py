"""Create the ``project_state`` table (static, from the ProjectState ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "project_0003_project_state"
down_revision = "project_0002_project_skill"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_state",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("direction", sa.String(), nullable=False),
        sa.Column("state_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("project_state")
