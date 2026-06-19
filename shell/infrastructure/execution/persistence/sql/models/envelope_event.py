from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shell.infrastructure.platform.persistence.sql.models.base import Base


class EnvelopeEventModel(Base):
    __tablename__ = "envelope_event"

    id: Mapped[str] = mapped_column(primary_key=True)
    envelope_id: Mapped[str] = mapped_column(
        ForeignKey("envelope.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    envelope: Mapped[EnvelopeModel] = relationship("EnvelopeModel", back_populates="events")


from shell.infrastructure.execution.persistence.sql.models.envelope import EnvelopeModel
