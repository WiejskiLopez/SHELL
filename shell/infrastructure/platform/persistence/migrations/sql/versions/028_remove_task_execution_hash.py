"""Remove hash column from task_execution — no content to hash.

Revision ID: 028
Revises: 027
Create Date: 2026-06-22

* Drop ``task_execution.hash`` — was always empty placeholder (Hash.of(""))
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "028"
down_revision = "027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("task_execution") as batch:
        batch.drop_column("hash")


def downgrade() -> None:
    with op.batch_alter_table("task_execution") as batch:
        batch.add_column(sa.Column("hash", sa.String(64), nullable=False, server_default=""))
