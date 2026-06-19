from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class SessionModel(Base):
    __tablename__ = "session"

    id: Mapped[str] = mapped_column(primary_key=True)
    goal: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="open")
    opened_at: Mapped[datetime] = mapped_column(nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    messages: Mapped[list[MessageModel]] = relationship(
        "MessageModel", back_populates="session", cascade="all, delete-orphan"
    )


from .message import MessageModel
