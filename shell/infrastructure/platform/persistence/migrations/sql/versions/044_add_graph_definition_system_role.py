"""Add system_role column to graph_definition table.

Revision ID: 044
Revises: 043
Create Date: 2026-06-28

* Add ``system_role`` column (VARCHAR(50), nullable, unique) to ``graph_definition``
* Allows marking a definition as the system default for a given role (PLANNER, DEVELOPER, TESTER)
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "044"
down_revision = "043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("graph_definition") as batch:
        batch.add_column(sa.Column("system_role", sa.String(50), nullable=True))
        batch.create_unique_constraint(
            "uq_graph_definition_system_role", ["system_role"],
        )


def downgrade() -> None:
    with op.batch_alter_table("graph_definition") as batch:
        batch.drop_constraint("uq_graph_definition_system_role", type_="unique")
        batch.drop_column("system_role")
