"""Add message_context column and missing timestamps to message_router.

Revision ID: 067
Revises: 066
Create Date: 2026-08-01

* ``message_router``: add ``message_context`` (JSON/JSONB) storing the
  routing context, required and read as ``JsonStr`` alongside ``message_data``.
* ``message_router``: backfill ``updated_at``/``deleted_at`` which the model
  and repository require but migration 059 omitted.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "067"
down_revision = "066"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("message_router") as batch:
        batch.add_column(sa.Column("message_context", sa.JSON, nullable=False, server_default="{}"))
        batch.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("message_router") as batch:
        batch.drop_column("deleted_at")
        batch.drop_column("updated_at")
        batch.drop_column("message_context")
