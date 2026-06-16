"""Faza 9 — adds RAG and session tables.

Revision ID: 002
Revises: 001
Create Date: 2026-06-05
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rag_document",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_uri", sa.String(1024), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("domain", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_rag_document_source_uri", "rag_document", ["source_uri"])
    op.create_index("ix_rag_document_domain", "rag_document", ["domain"])

    op.create_table(
        "rag_chunk",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "document_id",
            sa.String(36),
            sa.ForeignKey("rag_document.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("embedding", sa.LargeBinary, nullable=False),
        sa.Column("embedding_model", sa.String(128), nullable=False),
    )
    op.create_index("ix_rag_chunk_document_id", "rag_chunk", ["document_id"])

    op.create_table(
        "session",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("goal", sa.Text, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "message",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("session.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sender", sa.String(255), nullable=False),
        sa.Column("receiver", sa.String(255), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_message_session_id", "message", ["session_id"])


def downgrade() -> None:
    op.drop_table("message")
    op.drop_table("session")
    op.drop_table("rag_chunk")
    op.drop_table("rag_document")
