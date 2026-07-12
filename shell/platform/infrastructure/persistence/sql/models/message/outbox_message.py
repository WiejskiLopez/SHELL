from __future__ import annotations

from datetime import datetime  # noqa: TC003 -- Mapped[datetime] wymaga datetime w runtime

from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB
from shell.platform.infrastructure.persistence.sql.models.base import Base


class OutboxMessageModel(Base):
    __tablename__ = "outbox_message"

    __table_args__ = (Index("ix_outbox_message_published_at", "published_at"),)

    id: Mapped[str] = mapped_column(primary_key=True)
    envelope: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
