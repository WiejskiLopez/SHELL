from __future__ import annotations

from datetime import datetime  # noqa: TC003 -- Mapped[datetime] requires datetime at runtime

from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB
from shell.platform.infrastructure.persistence.sql.models.base import Base


class MessageModel(Base):
    __tablename__ = "message"

    __table_args__ = (
        Index("ix_message_workflow_id", "workflow_id"),
        Index("ix_message_source", "source"),
        Index("ix_message_destination", "destination"),
        Index("ix_message_status", "status"),
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    message_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    # Legacy columns — do not use in new code, kept for backward compat
    message_type: Mapped[str] = mapped_column(nullable=False)
    business_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    message_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    source: Mapped[str] = mapped_column(nullable=False)
    destination: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="created")
    workflow_id: Mapped[str | None] = mapped_column(nullable=True)
    step: Mapped[int | None] = mapped_column(nullable=True)
    sequence_id: Mapped[int | None] = mapped_column(nullable=True)
    source_node_execution_id: Mapped[str | None] = mapped_column(nullable=True)
    target_node_execution_id: Mapped[str | None] = mapped_column(nullable=True)
    source_role: Mapped[str | None] = mapped_column(nullable=True)
    target_role: Mapped[str | None] = mapped_column(nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(nullable=True)
