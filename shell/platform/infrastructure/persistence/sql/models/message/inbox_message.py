from __future__ import annotations

from datetime import datetime  # noqa: TC003 -- Mapped[datetime] wymaga datetime w runtime

from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB
from shell.platform.infrastructure.persistence.sql.models.base import Base


class InboxMessageModel(Base):
    __tablename__ = "inbox_message"

    __table_args__ = (Index("ix_inbox_message_processed_at", "processed_at"),)

    id: Mapped[str] = mapped_column(primary_key=True)
    message_type: Mapped[str] = mapped_column(nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
    causation_id: Mapped[str] = mapped_column(nullable=False, default="")
    received_at: Mapped[datetime] = mapped_column(nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0)
    last_attempted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    error: Mapped[str | None] = mapped_column(nullable=True)
