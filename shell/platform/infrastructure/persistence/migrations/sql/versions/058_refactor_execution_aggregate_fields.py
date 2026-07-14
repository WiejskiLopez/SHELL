"""Refactor execution and definition aggregate fields.

Revision ID: 058
Revises: 057
Create Date: 2026-07-14

* ``agent_config_execution``: drop ``session_execution_id``, ``user_execution_id``,
  ``model``, ``temperature``, ``max_tokens``, ``top_p``; add ``config_data`` (JSON string)
* ``agent_execution``: add ``updated_at`` column
* ``node_execution``: drop ``position``, ``mode``, ``role`` columns
* ``node_definition``: drop ``mode``, ``role`` columns
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "058"
down_revision = "057"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── agent_config_execution ─────────────────────────────────────────────────
    with op.batch_alter_table("agent_config_execution") as batch:
        batch.drop_column("session_execution_id")
        batch.drop_column("user_execution_id")
        batch.drop_column("model")
        batch.drop_column("temperature")
        batch.drop_column("max_tokens")
        batch.drop_column("top_p")
        batch.add_column(sa.Column("config_data", sa.String(), nullable=False, server_default="{}"))

    # ── agent_execution ────────────────────────────────────────────────────────
    with op.batch_alter_table("agent_execution") as batch:
        batch.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))

    # ── node_execution ─────────────────────────────────────────────────────────
    with op.batch_alter_table("node_execution") as batch:
        batch.drop_column("position")
        batch.drop_column("mode")
        batch.drop_column("role")
        batch.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))

    # ── node_definition ────────────────────────────────────────────────────────
    with op.batch_alter_table("node_definition") as batch:
        batch.drop_column("mode")
        batch.drop_column("role")


def downgrade() -> None:
    # ── node_definition ────────────────────────────────────────────────────────
    with op.batch_alter_table("node_definition") as batch:
        batch.add_column(sa.Column("role", sa.String(), nullable=False, server_default=""))
        batch.add_column(sa.Column("mode", sa.String(), nullable=False, server_default=""))

    # ── node_execution ─────────────────────────────────────────────────────────
    with op.batch_alter_table("node_execution") as batch:
        batch.add_column(sa.Column("role", sa.String(), nullable=False, server_default=""))
        batch.add_column(sa.Column("mode", sa.String(), nullable=False, server_default=""))
        batch.add_column(sa.Column("position", sa.Integer(), nullable=False, server_default="0"))

    # ── agent_execution ────────────────────────────────────────────────────────
    with op.batch_alter_table("agent_execution") as batch:
        batch.drop_column("updated_at")

    # ── agent_config_execution ─────────────────────────────────────────────────
    with op.batch_alter_table("agent_config_execution") as batch:
        batch.drop_column("config_data")
        batch.add_column(sa.Column("top_p", sa.Float(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("temperature", sa.Float(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("model", sa.String(), nullable=False, server_default=""))
        batch.add_column(sa.Column("user_execution_id", sa.String(), nullable=True))
        batch.add_column(sa.Column("session_execution_id", sa.String(), nullable=True))
