from __future__ import annotations

import sqlalchemy as sa
from alembic import context, op

revision = "platform_0008_saga_instance"
down_revision = "platform_0007_worker_heartbeat"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if context.config.get_main_option("include_saga") != "true":
        return
    op.create_table(
        "saga_instance",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("saga_type", sa.String(), nullable=False),
        sa.Column("saga_key", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("current_step", sa.String(), nullable=True),
        sa.Column("business_payload", sa.JSON(), nullable=False),
        sa.Column("completed_steps", sa.JSON(), nullable=False),
        sa.Column("failed_steps", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("compensated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("saga_type", "saga_key", name="uq_saga_instance_type_key"),
    )
    op.create_index(
        "ix_saga_instance_status_current",
        "saga_instance",
        ["status", "current_step"],
    )


def downgrade() -> None:
    if context.config.get_main_option("include_saga") != "true":
        return
    op.drop_index("ix_saga_instance_status_current", table_name="saga_instance")
    op.drop_table("saga_instance")
