from __future__ import annotations

from datetime import datetime

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from shell.infrastructure.platform.persistence.sql.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column


class OutboxCommandModel(Base):
    __tablename__ = "outbox_command"

    id: Mapped[str] = mapped_column(primary_key=True)
    command_type: Mapped[str] = mapped_column(nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
    causation_id: Mapped[str] = mapped_column(nullable=False, default="")
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
