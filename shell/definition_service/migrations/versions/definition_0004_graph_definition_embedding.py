"""Create the ``graph_definition_embedding`` table (static, from the ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "definition_0004_graph_definition_embedding"
down_revision = "definition_0003_runner_config"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "graph_definition_embedding",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("graph_definition_id", sa.String(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("embedding", sa.LargeBinary(), nullable=False),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["graph_definition_id"],
            ["graph_definition.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "graph_definition_id",
            name="uq_graph_definition_embedding_graph_definition_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("graph_definition_embedding")
