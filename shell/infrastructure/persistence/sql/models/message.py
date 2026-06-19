from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class MessageModel(Base):
    __tablename__ = "message"

    id: Mapped[str] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("session.id", ondelete="CASCADE"), nullable=False, index=True
    )
    correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
    sender: Mapped[str] = mapped_column(nullable=False)
    receiver: Mapped[str] = mapped_column(nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    session: Mapped[SessionModel] = relationship("SessionModel", back_populates="messages")


from .session import SessionModel
