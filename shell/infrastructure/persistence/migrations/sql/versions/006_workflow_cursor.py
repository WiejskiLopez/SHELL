"""Phase 14 — workflow cursor + execution context + optimistic locking.

Revision ID: 006
Revises: 005
Create Date: 2026-06-11

* Add ``workflow.current_node_id`` (nullable, indexed) — execution cursor.
* Add ``workflow.work_dir`` — captured execution context.
* Add ``workflow.correlation_id`` — captured execution context.
* Add ``workflow.version`` — optimistic concurrency token (CAS).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("workflow") as batch:
        batch.add_column(
            sa.Column("current_node_id", sa.String(255), nullable=True, server_default=None)
        )
        batch.add_column(
            sa.Column(
                "work_dir",
                sa.String(1024),
                nullable=False,
                server_default="",
            )
        )
        batch.add_column(
            sa.Column(
                "correlation_id",
                sa.String(64),
                nullable=False,
                server_default="",
            )
        )
        batch.add_column(
            sa.Column(
                "version",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch.create_index(
            "ix_workflow_current_node_id",
            ["current_node_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("workflow") as batch:
        batch.drop_index("ix_workflow_current_node_id")
        batch.drop_column("version")
        batch.drop_column("correlation_id")
        batch.drop_column("work_dir")
        batch.drop_column("current_node_id")
