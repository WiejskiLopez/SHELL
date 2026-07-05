"""Unify timestamps (created_at/updated_at/deleted_at) across all tables.

Revision ID: 050
Revises: 049
Create Date: 2026-07-05

Changes:
* Add ``updated_at`` and ``deleted_at`` columns to all tables that have ``created_at``
* Add ``created_at`` to ``session`` table (migrate from ``opened_at``)
* Migrate status-based soft-delete data to ``deleted_at``:
  - ``user``: status='disabled' → deleted_at = created_at
  - ``project``: status='archived' → deleted_at = created_at
* Drop ``closed_at`` from ``session`` (replaced by ``deleted_at``)
* Create ``project``, ``project_state``, ``project_skill`` tables (missing from prior migrations)
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "050"
down_revision = "049"
branch_labels = None
depends_on = None

TABLES_WITH_CREATED_AT = [
    "user",
    "user_state",
    "user_skill",
    "project",
    "project_state",
    "project_skill",
    "session_state",
    "workflow",
    "workflow_state",
    "task_execution",
    "task_execution_state",
    "session_execution",
    "session_execution_state",
    "user_execution",
    "user_execution_state",
    "node_execution",
    "node_execution_state",
    "node_link_execution",
    "node_transition_execution",
    "graph_execution",
    "graph_execution_state",
    "agent_execution",
    "agent_config_execution",
    "agent_skill_execution",
    "graph_definition",
    "node_definition",
    "node_link_definition",
    "node_transition_definition",
    "graph_definition_embedding",
    "rag_document",
    "scheduler_definition",
    "scheduler_execution",
    "scheduler_job",
    "message",
]


def upgrade() -> None:
    _create_project_tables()

    for table in TABLES_WITH_CREATED_AT:
        _add_timestamp_columns(table)

    if not _column_exists("session", "created_at"):
        op.add_column(
            "session",
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.execute("UPDATE session SET created_at = opened_at")
        with op.batch_alter_table("session") as batch_op:
            batch_op.alter_column("created_at", nullable=False)

    op.add_column(
        "session",
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.execute("UPDATE session SET deleted_at = closed_at WHERE closed_at IS NOT NULL")
    op.drop_column("session", "closed_at")

    op.execute("UPDATE user SET deleted_at = created_at WHERE status = 'disabled'")
    op.execute(
        "UPDATE project SET deleted_at = created_at WHERE status = 'archived'"
    )


def downgrade() -> None:
    for table in TABLES_WITH_CREATED_AT:
        _drop_timestamp_columns(table)

    op.add_column(
        "session",
        sa.Column("closed_at", sa.DateTime(), nullable=True),
    )
    op.execute("UPDATE session SET closed_at = deleted_at WHERE deleted_at IS NOT NULL")
    op.drop_column("session", "deleted_at")
    op.drop_column("session", "created_at")

    op.execute("UPDATE user SET deleted_at = NULL")
    op.execute("UPDATE project SET deleted_at = NULL")

    _drop_project_tables()


def _create_project_tables() -> None:
    if _table_exists("project"):
        return

    op.create_table(
        "project",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("repo_url", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "project_state",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("direction", sa.String(), nullable=False),
        sa.Column("state_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "project_skill",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("skill_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def _drop_project_tables() -> None:
    op.drop_table("project_skill")
    op.drop_table("project_state")
    op.drop_table("project")


def _table_exists(table: str) -> bool:
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)
    return table in inspector.get_table_names()


def _add_timestamp_columns(table: str) -> None:
    if not _table_exists(table):
        return

    with op.batch_alter_table(table) as batch_op:
        if not _column_exists(table, "updated_at"):
            batch_op.add_column(
                sa.Column("updated_at", sa.DateTime(), nullable=True)
            )
        if not _column_exists(table, "deleted_at"):
            batch_op.add_column(
                sa.Column("deleted_at", sa.DateTime(), nullable=True)
            )


def _drop_timestamp_columns(table: str) -> None:
    if not _table_exists(table):
        return

    with op.batch_alter_table(table) as batch_op:
        if _column_exists(table, "updated_at"):
            batch_op.drop_column("updated_at")
        if _column_exists(table, "deleted_at"):
            batch_op.drop_column("deleted_at")


def _column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    dialect = conn.dialect.name
    if dialect == "sqlite":
        from sqlalchemy import inspect

        inspector = inspect(conn)
        columns = [c["name"] for c in inspector.get_columns(table)]
        return column in columns
    if dialect == "postgresql":
        result = conn.execute(
            sa.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = :table AND column_name = :column"
            ),
            {"table": table, "column": column},
        )
        return result.fetchone() is not None
    return False