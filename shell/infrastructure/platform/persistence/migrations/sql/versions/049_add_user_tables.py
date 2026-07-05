"""Add user, user_skill, user_state tables.

Revision ID: 049
Revises: 048
Create Date: 2026-07-05

* Create ``user`` table (code replaces old identity, adds created_at)
* Create ``user_skill`` table (separate aggregate referencing user)
* Create ``user_state`` table (consolidates input/output with direction discriminator)
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "049"
down_revision = "048"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── user ─────────────────────────────────────────────────────────────────
    op.create_table(
        "user",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── user_skill ───────────────────────────────────────────────────────────
    op.create_table(
        "user_skill",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("skill_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── user_state ───────────────────────────────────────────────────────────
    op.create_table(
        "user_state",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("direction", sa.String(), nullable=False),
        sa.Column("state_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("user_state")
    op.drop_table("user_skill")
    op.drop_table("user")
