from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from shell.infrastructure.platform.persistence.sql.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship


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


from shell.infrastructure.platform.persistence.sql.models.message import (  # noqa: E402 — łamie circular import SessionModel ↔ MessageModel
    MessageModel,  # noqa: TC002 — MessageModel używany w Mapped[list[MessageModel]] w relacji SQLAlchemy
)
