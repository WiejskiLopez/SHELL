"""Remove legacy fields from multiple tables.

Revision ID: 055
Revises: 054
Create Date: 2026-07-13

Changes:
* DROP is_current from: user_state, project_state, task_execution_state,
  graph_execution_state_input, graph_execution_state_output,
  session_execution_state, user_execution_state, workflow_state, node_execution_state
* DROP environment_os, environment_runtime, environment_cwd from session
* ADD created_at (nullable DateTime) to graph_execution (updated_at/deleted_at already exist from 050)
* DROP session_execution_id from workflow
* DROP name, purpose, system_role from graph_definition
* DROP position, model, command, timeout, retries, log_level, no_ask_user,
  autopilot, status_initial, script, script_type from node_definition
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "055"
down_revision = "054"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop partial indexes that reference is_current BEFORE batch_alter_table,
    # because SQLite's table-copy mechanism would try to recreate them against
    # the new table where is_current no longer exists.
    op.drop_index(
        "uq_task_execution_state_task_id_direction_current",
        table_name="task_execution_state",
    )
    op.drop_index(
        "uq_graph_execution_state_input_is_current",
        table_name="graph_execution_state_input",
    )
    op.drop_index(
        "uq_graph_execution_state_output_is_current",
        table_name="graph_execution_state_output",
    )
    op.drop_index(
        "uq_node_execution_state_gnode_id_direction_current",
        table_name="node_execution_state",
    )

    # ── user_state ────────────────────────────────────────────────────────────
    with op.batch_alter_table("user_state") as batch_op:
        batch_op.drop_column("is_current")

    # ── project_state ─────────────────────────────────────────────────────────
    with op.batch_alter_table("project_state") as batch_op:
        batch_op.drop_column("is_current")

    # ── task_execution_state ──────────────────────────────────────────────────
    with op.batch_alter_table("task_execution_state") as batch_op:
        batch_op.drop_column("is_current")

    # ── graph_execution_state_input ───────────────────────────────────────────
    with op.batch_alter_table("graph_execution_state_input") as batch_op:
        batch_op.drop_column("is_current")

    # ── graph_execution_state_output ──────────────────────────────────────────
    with op.batch_alter_table("graph_execution_state_output") as batch_op:
        batch_op.drop_column("is_current")

    # ── session_execution_state ───────────────────────────────────────────────
    with op.batch_alter_table("session_execution_state") as batch_op:
        batch_op.drop_column("is_current")

    # ── user_execution_state ──────────────────────────────────────────────────
    with op.batch_alter_table("user_execution_state") as batch_op:
        batch_op.drop_column("is_current")

    # ── workflow_state ────────────────────────────────────────────────────────
    with op.batch_alter_table("workflow_state") as batch_op:
        batch_op.drop_column("is_current")

    # ── node_execution_state ──────────────────────────────────────────────────
    with op.batch_alter_table("node_execution_state") as batch_op:
        batch_op.drop_column("is_current")

    # ── session ───────────────────────────────────────────────────────────────
    with op.batch_alter_table("session") as batch_op:
        batch_op.drop_column("environment_os")
        batch_op.drop_column("environment_runtime")
        batch_op.drop_column("environment_cwd")

    # ── graph_execution ───────────────────────────────────────────────────────
    # Note: updated_at and deleted_at were already added by migration 050.
    # Only created_at is new here.
    with op.batch_alter_table("graph_execution") as batch_op:
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))

    # ── workflow ──────────────────────────────────────────────────────────────
    with op.batch_alter_table("workflow") as batch_op:
        batch_op.drop_column("session_execution_id")

    # ── graph_definition ──────────────────────────────────────────────────────
    with op.batch_alter_table("graph_definition") as batch_op:
        batch_op.drop_column("name")
        batch_op.drop_column("purpose")
        batch_op.drop_column("system_role")

    # ── node_definition ───────────────────────────────────────────────────────
    with op.batch_alter_table("node_definition") as batch_op:
        batch_op.drop_column("position")
        batch_op.drop_column("model")
        batch_op.drop_column("command")
        batch_op.drop_column("timeout")
        batch_op.drop_column("retries")
        batch_op.drop_column("log_level")
        batch_op.drop_column("no_ask_user")
        batch_op.drop_column("autopilot")
        batch_op.drop_column("status_initial")
        batch_op.drop_column("script")
        batch_op.drop_column("script_type")


def downgrade() -> None:
    # ── node_definition ───────────────────────────────────────────────────────
    with op.batch_alter_table("node_definition") as batch_op:
        batch_op.add_column(sa.Column("script_type", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("script", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("status_initial", sa.String(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("autopilot", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("no_ask_user", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("log_level", sa.String(), nullable=False, server_default="INFO"))
        batch_op.add_column(sa.Column("retries", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("timeout", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("command", sa.String(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("model", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("position", sa.Integer(), nullable=False, server_default="0"))

    # ── graph_definition ──────────────────────────────────────────────────────
    with op.batch_alter_table("graph_definition") as batch_op:
        batch_op.add_column(sa.Column("system_role", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("purpose", sa.String(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("name", sa.String(), nullable=False, server_default=""))

    # ── workflow ──────────────────────────────────────────────────────────────
    with op.batch_alter_table("workflow") as batch_op:
        batch_op.add_column(sa.Column("session_execution_id", sa.String(), nullable=True))

    # ── graph_execution ───────────────────────────────────────────────────────
    # Only drop created_at; updated_at and deleted_at belong to migration 050.
    with op.batch_alter_table("graph_execution") as batch_op:
        batch_op.drop_column("created_at")

    # ── session ───────────────────────────────────────────────────────────────
    with op.batch_alter_table("session") as batch_op:
        batch_op.add_column(sa.Column("environment_cwd", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("environment_runtime", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("environment_os", sa.String(), nullable=True))

    # ── node_execution_state ──────────────────────────────────────────────────
    with op.batch_alter_table("node_execution_state") as batch_op:
        batch_op.add_column(sa.Column("is_current", sa.Boolean(), nullable=False, server_default="0"))

    # ── workflow_state ────────────────────────────────────────────────────────
    with op.batch_alter_table("workflow_state") as batch_op:
        batch_op.add_column(sa.Column("is_current", sa.Boolean(), nullable=False, server_default="0"))

    # ── user_execution_state ──────────────────────────────────────────────────
    with op.batch_alter_table("user_execution_state") as batch_op:
        batch_op.add_column(sa.Column("is_current", sa.Boolean(), nullable=False, server_default="0"))

    # ── session_execution_state ───────────────────────────────────────────────
    with op.batch_alter_table("session_execution_state") as batch_op:
        batch_op.add_column(sa.Column("is_current", sa.Boolean(), nullable=False, server_default="0"))

    # ── graph_execution_state_output ──────────────────────────────────────────
    with op.batch_alter_table("graph_execution_state_output") as batch_op:
        batch_op.add_column(sa.Column("is_current", sa.Boolean(), nullable=False, server_default="0"))

    # ── graph_execution_state_input ───────────────────────────────────────────
    with op.batch_alter_table("graph_execution_state_input") as batch_op:
        batch_op.add_column(sa.Column("is_current", sa.Boolean(), nullable=False, server_default="0"))

    # ── task_execution_state ──────────────────────────────────────────────────
    with op.batch_alter_table("task_execution_state") as batch_op:
        batch_op.add_column(sa.Column("is_current", sa.Boolean(), nullable=False, server_default="0"))

    # ── project_state ─────────────────────────────────────────────────────────
    with op.batch_alter_table("project_state") as batch_op:
        batch_op.add_column(sa.Column("is_current", sa.Boolean(), nullable=False, server_default="0"))

    # ── user_state ────────────────────────────────────────────────────────────
    with op.batch_alter_table("user_state") as batch_op:
        batch_op.add_column(sa.Column("is_current", sa.Boolean(), nullable=False, server_default="0"))

    # Recreate partial indexes that were dropped in upgrade()
    op.create_index(
        "uq_task_execution_state_task_id_direction_current",
        "task_execution_state",
        ["task_execution_id", "direction"],
        postgresql_where=sa.text("is_current = true"),
        sqlite_where=sa.text("is_current = 1"),
        unique=True,
    )
    op.create_index(
        "uq_graph_execution_state_input_is_current",
        "graph_execution_state_input",
        ["graph_execution_id"],
        postgresql_where=sa.text("is_current = true"),
        sqlite_where=sa.text("is_current = 1"),
        unique=True,
    )
    op.create_index(
        "uq_graph_execution_state_output_is_current",
        "graph_execution_state_output",
        ["graph_execution_id"],
        postgresql_where=sa.text("is_current = true"),
        sqlite_where=sa.text("is_current = 1"),
        unique=True,
    )
    op.create_index(
        "uq_node_execution_state_gnode_id_direction_current",
        "node_execution_state",
        ["node_execution_id", "direction"],
        postgresql_where=sa.text("is_current = true"),
        sqlite_where=sa.text("is_current = 1"),
        unique=True,
    )
