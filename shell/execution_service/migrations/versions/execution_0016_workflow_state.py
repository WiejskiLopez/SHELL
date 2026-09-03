"""Create the ``workflow_state`` table (static, from the WorkflowState ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "execution_0016_workflow_state"
down_revision = "execution_0015_user_execution_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_state",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("workflow_id", sa.String(), nullable=False),
        sa.Column("direction", sa.String(), nullable=False),
        sa.Column("state_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflow.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("workflow_state")
