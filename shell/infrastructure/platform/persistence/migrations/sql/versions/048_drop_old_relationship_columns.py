"""Drop old direct FK columns replaced by link tables.

Revision ID: 048
Revises: 047
Create Date: 2026-07-02

* Drop ``node_definition.graph_definition_id``
* Drop ``node_execution.graph_execution_id``
* Drop ``graph_execution.initialization_status``
* Drop ``graph_execution.node_definition_executions``
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "048"
down_revision = "047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("node_definition") as batch:
        batch.drop_index("ix_node_definition_graph_definition_id")
        batch.drop_column("graph_definition_id")

    with op.batch_alter_table("node_execution") as batch:
        batch.drop_index("ix_node_execution_graph_execution_id")
        batch.drop_column("graph_execution_id")

    with op.batch_alter_table("graph_execution") as batch:
        batch.drop_column("initialization_status")
        batch.drop_column("node_definition_executions")


def downgrade() -> None:
    with op.batch_alter_table("graph_execution") as batch:
        batch.add_column(
            sa.Column("node_definition_executions", sa.JSON(), nullable=False, server_default="{}")
        )
        batch.add_column(
            sa.Column(
                "initialization_status", sa.String(), nullable=False, server_default="pending"
            )
        )

    with op.batch_alter_table("node_execution") as batch:
        batch.add_column(sa.Column("graph_execution_id", sa.String(), nullable=True))

    with op.batch_alter_table("node_definition") as batch:
        batch.add_column(sa.Column("graph_definition_id", sa.String(), nullable=True))
