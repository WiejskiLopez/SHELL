from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "platform_0004_inbox_command"
down_revision = "platform_0003_outbox_command"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inbox_command",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("outbox_id", sa.String(), nullable=False),
        sa.Column("command_id", sa.String(), nullable=False),
        sa.Column("command_name", sa.String(), nullable=False),
        sa.Column("source_service", sa.String(), nullable=False),
        sa.Column("target_service", sa.String(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.UniqueConstraint(
            "source_service",
            "outbox_id",
            name="uq_inbox_command_source_outbox",
        ),
    )
    op.create_index(
        "ix_inbox_command_status_next_attempt_received",
        "inbox_command",
        ["status", "next_attempt_at", "received_at"],
    )
    op.create_index(
        "ix_inbox_command_status_lease_until", "inbox_command", ["status", "lease_until"]
    )


def downgrade() -> None:
    op.drop_index("ix_inbox_command_status_lease_until", table_name="inbox_command")
    op.drop_index("ix_inbox_command_status_next_attempt_received", table_name="inbox_command")
    op.drop_table("inbox_command")
