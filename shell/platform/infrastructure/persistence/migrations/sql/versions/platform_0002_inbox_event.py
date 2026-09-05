from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "platform_0002_inbox_event"
down_revision = "platform_0001_outbox_event"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_inbox",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("source_service", sa.String(), nullable=False),
        sa.Column("integration_event_name", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("aggregate_id", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("correlation_id", sa.String(), nullable=False),
        sa.Column("causation_id", sa.String(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claimed_by", sa.String(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("error_code", sa.String(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.UniqueConstraint("source_service", "event_id", name="uq_event_inbox_source_event"),
    )
    op.create_index(
        "ix_event_inbox_status_next_attempt_received",
        "event_inbox",
        ["status", "next_attempt_at", "received_at"],
    )
    op.create_index("ix_event_inbox_status_lease_until", "event_inbox", ["status", "lease_until"])


def downgrade() -> None:
    op.drop_index("ix_event_inbox_status_lease_until", table_name="event_inbox")
    op.drop_index("ix_event_inbox_status_next_attempt_received", table_name="event_inbox")
    op.drop_table("event_inbox")
