from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "platform_0006_processed_delivery"
down_revision = "platform_0005_audit_event"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "processed_delivery",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("consumer_name", sa.String(), nullable=False),
        sa.Column("outbox_id", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "consumer_name",
            "outbox_id",
            name="uq_processed_delivery_consumer_outbox",
        ),
    )


def downgrade() -> None:
    op.drop_table("processed_delivery")
