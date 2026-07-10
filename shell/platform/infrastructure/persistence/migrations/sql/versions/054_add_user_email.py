"""Add email column and drop code column from user table.

Revision ID: 054
Revises: 053
Create Date: 2026-07-06

* Add ``email`` column (non-nullable)
* Drop ``code`` column
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "054"
down_revision = "053"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add email as nullable first to handle existing rows, then make non-nullable
    with op.batch_alter_table("user") as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(), nullable=True))

    # Backfill existing rows
    op.execute("UPDATE \"user\" SET email = id || '@placeholder.invalid' WHERE email IS NULL")

    with op.batch_alter_table("user") as batch_op:
        batch_op.alter_column("email", nullable=False)
        batch_op.drop_column("code")


def downgrade() -> None:
    with op.batch_alter_table("user") as batch_op:
        batch_op.add_column(sa.Column("code", sa.String(), nullable=False, server_default=""))
        batch_op.drop_column("email")
