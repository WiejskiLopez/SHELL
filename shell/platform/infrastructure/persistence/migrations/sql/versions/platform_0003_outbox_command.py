from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "platform_0003_outbox_command"
down_revision = "platform_0002_inbox_event"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox_command",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("command_id", sa.String(), nullable=False),
        sa.Column("command_name", sa.String(), nullable=False),
        sa.Column("source_service", sa.String(), nullable=False),
        sa.Column("target_service", sa.String(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("correlation_id", sa.String(), nullable=False),
        sa.Column("causation_id", sa.String(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("source_service", "command_id", name="uq_outbox_command_source_cmd"),
    )
    op.create_index(
        "ix_outbox_command_publish",
        "outbox_command",
        ["published_at", "issued_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_command_publish", table_name="outbox_command")
    op.drop_table("outbox_command")
