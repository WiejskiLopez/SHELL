from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "platform_0009_saga_timeout"
down_revision = "platform_0008_saga_instance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saga_timeout",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("outbox_id", sa.String(), nullable=False),
        sa.Column("saga_id", sa.String(), nullable=False),
        sa.Column("saga_key", sa.String(), nullable=False),
        sa.Column("step", sa.String(), nullable=False),
        sa.Column("source_service", sa.String(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.UniqueConstraint("source_service", "outbox_id", name="uq_saga_timeout_source_outbox"),
    )
    op.create_index(
        "ix_saga_timeout_status_next_attempt_received",
        "saga_timeout",
        ["status", "next_attempt_at", "received_at"],
    )
    op.create_index("ix_saga_timeout_status_lease_until", "saga_timeout", ["status", "lease_until"])


def downgrade() -> None:
    op.drop_index("ix_saga_timeout_status_lease_until", table_name="saga_timeout")
    op.drop_index("ix_saga_timeout_status_next_attempt_received", table_name="saga_timeout")
    op.drop_table("saga_timeout")
