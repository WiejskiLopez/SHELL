from __future__ import annotations

from datetime import datetime  # noqa: TC003 -- Mapped[datetime] wymaga datetime w runtime

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from shell.infrastructure.platform.persistence.sql.models.base import Base
from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column


class OutboxMessageModel(Base):
    __tablename__ = "outbox_message"

    __table_args__ = (
        Index("ix_outbox_message_published_at", "published_at"),
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    envelope: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
