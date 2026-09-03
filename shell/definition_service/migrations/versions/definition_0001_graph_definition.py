"""Create the ``graph_definition`` table (static, from the GraphDefinition ORM model)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "definition_0001_graph_definition"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "graph_definition",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("graph_definition")
