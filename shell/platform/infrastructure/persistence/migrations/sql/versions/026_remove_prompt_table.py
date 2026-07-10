"""Remove prompt table — domain prompt concept removed.

Revision ID: 026
Revises: 025
Create Date: 2026-06-22

* Drop ``prompt`` table
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "026"
down_revision = "025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_prompt_name", table_name="prompt")
    op.drop_table("prompt")


def downgrade() -> None:
    op.create_table(
        "prompt",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("source_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prompt_name", "prompt", ["name"])
