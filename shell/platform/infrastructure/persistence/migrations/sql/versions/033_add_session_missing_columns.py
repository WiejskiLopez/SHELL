"""Add user_id/project_id/environment columns to session table.

Session aggregate root stores user_id, project_id, and environment
fields that were missing from the SQL model.  This migration adds them
so that session_model_to_entity can perform a proper round-trip.

Revision ID: 033
Revises: 032
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "033"
down_revision = "032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("session") as batch:
        batch.add_column(sa.Column("user_id", sa.String(255), nullable=False, server_default=""))
        batch.add_column(sa.Column("project_id", sa.String(255), nullable=False, server_default=""))
        batch.add_column(
            sa.Column("environment_os", sa.String(64), nullable=False, server_default="")
        )
        batch.add_column(
            sa.Column("environment_runtime", sa.String(64), nullable=False, server_default="")
        )
        batch.add_column(
            sa.Column("environment_cwd", sa.String(1024), nullable=False, server_default="")
        )


def downgrade() -> None:
    with op.batch_alter_table("session") as batch:
        batch.drop_column("environment_cwd")
        batch.drop_column("environment_runtime")
        batch.drop_column("environment_os")
        batch.drop_column("project_id")
        batch.drop_column("user_id")
