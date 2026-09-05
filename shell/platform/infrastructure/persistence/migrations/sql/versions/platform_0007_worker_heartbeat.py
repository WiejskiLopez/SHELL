from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "platform_0007_worker_heartbeat"
down_revision = "platform_0005_audit_event"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "worker_heartbeat",
        sa.Column("worker_id", sa.String(), primary_key=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("worker_heartbeat")
