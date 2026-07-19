"""Make created_at non-nullable across all tables.

Revision ID: 062
Revises: 061
Create Date: 2026-07-19

* Change ``graph_execution.created_at`` from nullable to non-nullable
* Change ``node_execution.created_at`` from nullable to non-nullable
* Add ``graph_definition.created_at`` column (non-nullable)
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "062"
down_revision = "061"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("graph_execution") as batch:
        batch.alter_column("created_at", existing_type=sa.DateTime(), nullable=False)

    with op.batch_alter_table("node_execution") as batch:
        batch.alter_column("created_at", existing_type=sa.DateTime(), nullable=False)

    with op.batch_alter_table("graph_definition") as batch:
        batch.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("'2024-01-01T00:00:00+00:00'"),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("graph_execution") as batch:
        batch.alter_column("created_at", existing_type=sa.DateTime(), nullable=True)

    with op.batch_alter_table("node_execution") as batch:
        batch.alter_column("created_at", existing_type=sa.DateTime(), nullable=True)

    with op.batch_alter_table("graph_definition") as batch:
        batch.drop_column("created_at")
