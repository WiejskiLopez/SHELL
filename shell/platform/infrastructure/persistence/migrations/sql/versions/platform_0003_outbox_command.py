from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "platform_0003_outbox_command"
down_revision = "platform_0002_inbox_event"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "command_outbox",
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
        sa.UniqueConstraint("source_service", "command_id", name="uq_command_outbox_source_cmd"),
    )
    op.create_index(
        "ix_command_outbox_publish",
        "command_outbox",
        ["published_at", "issued_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_command_outbox_publish", table_name="command_outbox")
    op.drop_table("command_outbox")
