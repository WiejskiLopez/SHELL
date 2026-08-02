"""Add updated_at column to session.

Revision ID: 068
Revises: 067
Create Date: 2026-08-02

* ``session``: backfill ``updated_at`` which the ORM model and mappers require
  but migration 050 omitted (session was not in ``TABLES_WITH_CREATED_AT``).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "068"
down_revision = "067"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("session") as batch:
        batch.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("session") as batch:
        batch.drop_column("updated_at")
