"""Create the ``ingestion`` table (static, from the Ingestion ORM model).

``ingestion_data`` and ``ingestion_context`` map the domain ``JsonStr`` via the
platform ``JsonStrType``, whose storage is a JSON/JSONB column.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "ingestion_0001_ingestion"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("ingestion_data", sa.JSON(), nullable=False),
        sa.Column("ingestion_context", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ingestion")
