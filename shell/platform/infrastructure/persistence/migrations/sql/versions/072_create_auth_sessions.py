"""Create auth_sessions table.

Revision ID: 072
Revises: 071
Create Date: 2026-08-09

* Create ``auth_sessions`` table for the AuthSession aggregate
* ``user_id`` references ``user.id``
* ``token_hash`` stores only the SHA-256 hash of the session token
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "072"
down_revision = "071"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("auth_sessions")
