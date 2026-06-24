"""Drop unused timeout column from graph_node_execution — use timeout_seconds instead.

Revision ID: 030
Revises: 029
Create Date: 2026-06-24

* Drop ``graph_node_execution.timeout`` — replaced by ``timeout_seconds``
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "030"
down_revision = "029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("graph_node_execution") as batch:
        batch.drop_column("timeout")


def downgrade() -> None:
    with op.batch_alter_table("graph_node_execution") as batch:
        batch.add_column(sa.Column("timeout", sa.Integer(), nullable=False, server_default="0"))
