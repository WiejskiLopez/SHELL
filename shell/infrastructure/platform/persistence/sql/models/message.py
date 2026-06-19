from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shell.infrastructure.platform.persistence.sql.models.base import Base


class MessageModel(Base):
    __tablename__ = "message"

    id: Mapped[str] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("session.id", ondelete="CASCADE"), nullable=False, index=True
    )
    correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
    sender: Mapped[str] = mapped_column(nullable=False)
    receiver: Mapped[str] = mapped_column(nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    session: Mapped[SessionModel] = relationship("SessionModel", back_populates="messages")


from shell.infrastructure.execution.persistence.sql.models.session import SessionModel
