from __future__ import annotations

from datetime import datetime

from ._compat import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AuditEventModel(Base):
    __tablename__ = "audit_event"

    id: Mapped[str] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
