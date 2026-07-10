"""Add session_id column to workflow for V2 Session→Workflow link.

Revision ID: 029
Revises: 028
Create Date: 2026-06-22

* Add ``workflow.session_id`` — nullable FK to session table
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "029"
down_revision = "028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("workflow") as batch:
        batch.add_column(sa.Column("session_id", sa.String(36), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("workflow") as batch:
        batch.drop_column("session_id")
