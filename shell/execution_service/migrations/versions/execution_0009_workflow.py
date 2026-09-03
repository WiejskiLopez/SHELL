"""Create the ``workflow`` table (static, from the Workflow ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "execution_0009_workflow"
down_revision = "execution_0008_user_execution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("workflow")
