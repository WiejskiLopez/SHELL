from __future__ import annotations

from datetime import datetime  # noqa: TC003 -- Mapped[datetime] wymaga datetime w runtime

from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from shell.infrastructure.platform.persistence.sql.models.base import Base


class InboxMessageModel(Base):
    __tablename__ = "inbox_message"

    __table_args__ = (Index("ix_inbox_message_processed_at", "processed_at"),)

    id: Mapped[str] = mapped_column(primary_key=True)
    envelope: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    received_at: Mapped[datetime] = mapped_column(nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    error: Mapped[str | None] = mapped_column(nullable=True)
