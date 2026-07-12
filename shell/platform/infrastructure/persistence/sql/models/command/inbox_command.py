from __future__ import annotations

from datetime import datetime  # noqa: TC003 — needed by SQLAlchemy declarative at runtime

from sqlalchemy.orm import Mapped, mapped_column

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB
from shell.platform.infrastructure.persistence.sql.models.base import Base


class InboxCommandModel(Base):
    __tablename__ = "inbox_command"

    id: Mapped[str] = mapped_column(primary_key=True)
    command_type: Mapped[str] = mapped_column(nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
    causation_id: Mapped[str] = mapped_column(nullable=False, default="")
    received_at: Mapped[datetime] = mapped_column(nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(nullable=True)
