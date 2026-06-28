"""Create graph_definition_embedding table for vector search.

Revision ID: 043
Revises: 042
Create Date: 2026-06-28

* Create ``graph_definition_embedding`` table
* Unique constraint on ``graph_definition_id`` (1:1 with graph_definition)
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "043"
down_revision = "042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "graph_definition_embedding",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "graph_definition_id",
            sa.String(),
            sa.ForeignKey("graph_definition.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("embedding", sa.LargeBinary(), nullable=False),
        sa.Column("embedding_model", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )


def downgrade() -> None:
    op.drop_table("graph_definition_embedding")
