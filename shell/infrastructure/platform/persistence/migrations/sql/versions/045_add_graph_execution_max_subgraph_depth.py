"""Add max_subgraph_depth column to graph_execution table.

Revision ID: 045
Revises: 044
Create Date: 2026-06-30

* Add ``max_subgraph_depth`` column (Integer, not null, default 5) to ``graph_execution``
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "045"
down_revision = "044"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("graph_execution") as batch:
        batch.add_column(
            sa.Column(
                "max_subgraph_depth", sa.Integer(), nullable=False, server_default=sa.text("5")
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("graph_execution") as batch:
        batch.drop_column("max_subgraph_depth")
