"""Initial migration — creates all shell tables.

Revision ID: 001
Revises:
Create Date: 2026-06-04
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_execution",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column("task_text", sa.Text, nullable=False, server_default=""),
        sa.Column("graph_definition_id", sa.String(36), nullable=False),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_task_execution_name", "task_execution", ["name"])

    op.create_table(
        "graph_execution",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "task_execution_id",
            sa.String(36),
            sa.ForeignKey("task_execution.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_graph_execution_task_execution_id", "graph_execution", ["task_execution_id"]
    )

    op.create_table(
        "node_execution",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "graph_execution_id",
            sa.String(36),
            sa.ForeignKey("graph_execution.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.Column("node_dir", sa.String(512), nullable=False, server_default=""),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("role", sa.String(128), nullable=False, server_default=""),
        sa.Column("node_type", sa.String(64), nullable=False, server_default=""),
        sa.Column("model", sa.String(128), nullable=False, server_default=""),
        sa.Column("command", sa.Text, nullable=False, server_default=""),
        sa.Column("timeout", sa.Integer, nullable=False, server_default="0"),
        sa.Column("retries", sa.Integer, nullable=False, server_default="0"),
        sa.Column("log_level", sa.String(16), nullable=False, server_default="INFO"),
        sa.Column("max_step", sa.Integer, nullable=False, server_default="0"),
        sa.Column("no_ask_user", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("autopilot", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("task_execution_id", sa.String(36), nullable=False, server_default=""),
        sa.Column("source_dir", sa.String(512), nullable=False, server_default=""),
        sa.Column("work_dir", sa.String(512), nullable=False, server_default=""),
        sa.Column("status_initial", sa.String(64), nullable=False, server_default=""),
        sa.Column("extra", sa.JSON, nullable=False, server_default="{}"),
    )
    op.create_index(
        "ix_node_execution_graph_execution_id", "node_execution", ["graph_execution_id"]
    )

    op.create_table(
        "workflow",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_execution_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="idle"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_workflow_task_execution_id", "workflow", ["task_execution_id"])

    op.create_table(
        "node_state",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "workflow_id",
            sa.String(36),
            sa.ForeignKey("workflow.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("graph_execution_id", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="idle"),
        sa.Column("step", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_node_state_workflow_id", "node_state", ["workflow_id"])

    op.create_table(
        "envelope",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workflow_id", sa.String(36), nullable=False),
        sa.Column("parent_id", sa.String(36), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=False, server_default=""),
        sa.Column("sender_node_execution_id", sa.String(255), nullable=False),
        sa.Column("receiver_node_execution_id", sa.String(255), nullable=False),
        sa.Column("source_role", sa.String(128), nullable=False, server_default=""),
        sa.Column("target_role", sa.String(128), nullable=False, server_default=""),
        sa.Column("sequence_id", sa.Integer, nullable=False, server_default="0"),
        sa.Column("step", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("stage", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("artifact_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("archive_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_envelope_workflow_id", "envelope", ["workflow_id"])

    op.create_table(
        "envelope_event",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "envelope_id",
            sa.String(36),
            sa.ForeignKey("envelope.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_envelope_event_envelope_id", "envelope_event", ["envelope_id"])

    op.create_table(
        "node_result",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("node_execution_id", sa.String(255), nullable=False),
        sa.Column("workflow_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("stdout", sa.Text, nullable=False, server_default=""),
        sa.Column("stderr", sa.Text, nullable=False, server_default=""),
        sa.Column("artifact_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_node_result_node_execution_id", "node_result", ["node_execution_id"])
    op.create_index("ix_node_result_workflow_id", "node_result", ["workflow_id"])

    op.create_table(
        "prompt",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("source_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prompt_name", "prompt", ["name"])

    op.create_table(
        "runner_config",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("package_name", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column("body", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_runner_config_package_name", "runner_config", ["package_name"])

    # Envelope archive (optional — used by FileSystemEnvelopeArchive but kept for SQL completeness)
    op.create_table(
        "envelope_archive",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("envelope_id", sa.String(36), nullable=False),
        sa.Column("workflow_id", sa.String(36), nullable=False),
        sa.Column("archive_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_envelope_archive_workflow_id", "envelope_archive", ["workflow_id"])
    op.create_index("ix_envelope_archive_envelope_id", "envelope_archive", ["envelope_id"])

    # Tabela graph_definition
    op.create_table(
        "graph_definition",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("purpose", sa.String(255), nullable=False),
    )

    # Tabela node_definition
    op.create_table(
        "node_definition",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "graph_definition_id",
            sa.String(36),
            sa.ForeignKey("graph_definition.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("role", sa.String(128), nullable=False),
        sa.Column("node_type", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("command", sa.Text, nullable=False),
        sa.Column("timeout", sa.Integer, nullable=False),
        sa.Column("retries", sa.Integer, nullable=False),
        sa.Column("log_level", sa.String(16), nullable=False),
        sa.Column("max_step", sa.Integer, nullable=True),
        sa.Column("no_ask_user", sa.Boolean, nullable=True),
        sa.Column("autopilot", sa.Boolean, nullable=True),
        sa.Column("status_initial", sa.String(64), nullable=False),
        sa.Column("extra", sa.JSON, nullable=True),
        sa.Column("script", sa.Text, nullable=True),
        sa.Column("script_type", sa.String(16), nullable=True),
    )

    op.create_index(
        "ix_node_definition_graph_definition_id",
        "node_definition",
        ["graph_definition_id"],
    )


def downgrade() -> None:
    op.drop_table("envelope_archive")
    op.drop_table("runner_config")
    op.drop_table("prompt")
    op.drop_table("node_result")
    op.drop_table("envelope_event")
    op.drop_table("envelope")
    op.drop_table("node_state")
    op.drop_table("workflow")
    op.drop_table("node_execution")
    op.drop_table("graph_execution")
    op.drop_table("task_execution")
    op.drop_table("graph_definition")
    op.drop_table("node_definition")
