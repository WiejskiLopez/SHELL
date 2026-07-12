from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from sqlalchemy.orm import Mapped, mapped_column

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB
from shell.platform.infrastructure.persistence.sql.models.base import Base


class AuditEventModel(Base):
    __tablename__ = "audit_event"

    id: Mapped[str] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
