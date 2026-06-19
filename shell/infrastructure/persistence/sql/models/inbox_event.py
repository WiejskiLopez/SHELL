from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class InboxEventModel(Base):
    __tablename__ = "inbox_event"

    id: Mapped[str] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    received_at: Mapped[datetime] = mapped_column(nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(nullable=True, index=True)
