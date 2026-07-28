"""Move project_id from session to workflow, make session_id non-nullable.

Revision ID: 064
Revises: 063
Create Date: 2026-07-27

* Add ``workflow.project_id`` — non-nullable string
* Make ``workflow.session_id`` NOT NULL
* Drop ``session.project_id``
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "064"
down_revision = "063"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("workflow") as batch:
        batch.add_column(sa.Column("project_id", sa.String(), nullable=False, server_default=""))
        batch.alter_column("session_id", existing_type=sa.String(), nullable=False)

    with op.batch_alter_table("session") as batch:
        batch.drop_column("project_id")


def downgrade() -> None:
    with op.batch_alter_table("session") as batch:
        batch.add_column(sa.Column("project_id", sa.String(255), nullable=False, server_default=""))

    with op.batch_alter_table("workflow") as batch:
        batch.alter_column("session_id", existing_type=sa.String(), nullable=True)
        batch.drop_column("project_id")
