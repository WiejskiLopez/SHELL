"""Replace message outbox/inbox envelope JSON with typed columns.

Revision ID: 066
Revises: 065
Create Date: 2026-08-01

* ``outbox_message``: drop ``envelope``/``created_at``, add ``message_type``,
  ``occurred_at``, ``payload``, ``correlation_id``, ``causation_id``
* ``inbox_message``: same columns plus ``retry_count``, ``last_attempted_at``
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "066"
down_revision = "065"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("outbox_message") as batch:
        batch.drop_column("envelope")
        batch.drop_column("created_at")
        batch.add_column(
            sa.Column("message_type", sa.String(128), nullable=False, server_default="")
        )
        batch.add_column(
            sa.Column(
                "occurred_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("'2024-01-01T00:00:00+00:00'"),
            )
        )
        batch.add_column(sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"))
        batch.add_column(
            sa.Column("correlation_id", sa.String(255), nullable=False, server_default="")
        )
        batch.add_column(
            sa.Column("causation_id", sa.String(255), nullable=False, server_default="")
        )

    op.create_index("ix_outbox_message_message_type", "outbox_message", ["message_type"])

    with op.batch_alter_table("inbox_message") as batch:
        batch.drop_column("envelope")
        batch.drop_column("created_at")
        batch.add_column(
            sa.Column("message_type", sa.String(128), nullable=False, server_default="")
        )
        batch.add_column(
            sa.Column(
                "occurred_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("'2024-01-01T00:00:00+00:00'"),
            )
        )
        batch.add_column(sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"))
        batch.add_column(
            sa.Column("correlation_id", sa.String(255), nullable=False, server_default="")
        )
        batch.add_column(
            sa.Column("causation_id", sa.String(255), nullable=False, server_default="")
        )
        batch.add_column(sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False))
        batch.add_column(sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index("ix_inbox_message_message_type", "inbox_message", ["message_type"])


def downgrade() -> None:
    op.drop_index("ix_inbox_message_message_type", table_name="inbox_message")

    with op.batch_alter_table("inbox_message") as batch:
        batch.drop_column("last_attempted_at")
        batch.drop_column("retry_count")
        batch.drop_column("causation_id")
        batch.drop_column("correlation_id")
        batch.drop_column("payload")
        batch.drop_column("occurred_at")
        batch.drop_column("message_type")
        batch.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("'2024-01-01T00:00:00+00:00'"),
            )
        )
        batch.add_column(sa.Column("envelope", sa.JSON(), nullable=False, server_default="{}"))

    op.drop_index("ix_outbox_message_message_type", table_name="outbox_message")

    with op.batch_alter_table("outbox_message") as batch:
        batch.drop_column("causation_id")
        batch.drop_column("correlation_id")
        batch.drop_column("payload")
        batch.drop_column("occurred_at")
        batch.drop_column("message_type")
        batch.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("'2024-01-01T00:00:00+00:00'"),
            )
        )
        batch.add_column(sa.Column("envelope", sa.JSON(), nullable=False, server_default="{}"))
