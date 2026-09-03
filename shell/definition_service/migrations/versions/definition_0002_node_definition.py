"""Create the ``node_definition`` table (static, from the NodeDefinition ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "definition_0002_node_definition"
down_revision = "definition_0001_graph_definition"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "node_definition",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("node_type", sa.String(), nullable=False),
        sa.Column("max_step", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("node_definition")
