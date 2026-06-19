from __future__ import annotations

from datetime import datetime

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from shell.infrastructure.platform.persistence.sql.models.base import Base


class OutboxEventModel(Base):
    __tablename__ = "outbox_event"

    id: Mapped[str] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True, index=True)
