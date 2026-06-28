"""Drop unused correlation_id column from workflow table.

Revision ID: 040
Revises: 039
Create Date: 2026-06-27

* Drop ``workflow.correlation_id`` — unused in V2, tracing uses graph_execution.correlation_id
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "040"
down_revision = "039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("workflow") as batch:
        batch.drop_column("correlation_id")


def downgrade() -> None:
    with op.batch_alter_table("workflow") as batch:
        batch.add_column(
            sa.Column(
                "correlation_id",
                sa.String(64),
                nullable=False,
                server_default="",
            )
        )
