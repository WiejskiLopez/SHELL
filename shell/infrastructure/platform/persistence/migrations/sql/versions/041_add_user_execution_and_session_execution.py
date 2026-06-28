"""Add user_execution, user_execution_state, session_execution, session_execution_state tables + workflow.session_execution_id.

Revision ID: 041
Revises: 040
Create Date: 2026-06-27

* Create ``user_execution`` table
* Create ``user_execution_state`` table
* Create ``session_execution`` table
* Create ``session_execution_state`` table
* Add ``workflow.session_execution_id`` column
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "041"
down_revision = "040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── user_execution ─────────────────────────────────────────────────────
    op.create_table(
        "user_execution",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── user_execution_state ───────────────────────────────────────────────
    op.create_table(
        "user_execution_state",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_execution_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_execution_id"],
            ["user_execution.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── session_execution ──────────────────────────────────────────────────
    op.create_table(
        "session_execution",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_execution_id", sa.String(), nullable=True),
        sa.Column("session_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── session_execution_state ────────────────────────────────────────────
    op.create_table(
        "session_execution_state",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("session_execution_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_execution_id"],
            ["session_execution.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── workflow.session_execution_id ─────────────────────────────────────
    with op.batch_alter_table("workflow") as batch:
        batch.add_column(
            sa.Column("session_execution_id", sa.String(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("workflow") as batch:
        batch.drop_column("session_execution_id")

    op.drop_table("session_execution_state")
    op.drop_table("session_execution")
    op.drop_table("user_execution_state")
    op.drop_table("user_execution")
