from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "platform_0005_audit_event"
down_revision = "platform_0004_inbox_command"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_event",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("integration_event_name", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_event")
