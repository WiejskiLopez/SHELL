"""Create the ``node_link_definition`` table (static, from the ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "definition_0005_node_link_definition"
down_revision = "definition_0004_graph_definition_embedding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "node_link_definition",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("graph_definition_id", sa.String(), nullable=False),
        sa.Column("node_definition_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["graph_definition_id"],
            ["graph_definition.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["node_definition_id"],
            ["node_definition.id"],
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    op.drop_table("node_link_definition")
