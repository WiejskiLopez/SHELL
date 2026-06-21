from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from shell.infrastructure.platform.persistence.sql.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class MessageModel(Base):
    __tablename__ = "message"

    id: Mapped[str] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("session.id", ondelete="CASCADE"), nullable=False
    )
    correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
    sender: Mapped[str] = mapped_column(nullable=False)
    receiver: Mapped[str] = mapped_column(nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    session: Mapped[SessionModel] = relationship("SessionModel", back_populates="messages")


from shell.infrastructure.execution.persistence.sql.models.session import (  # noqa: E402 — łamie circular import MessageModel ↔ SessionModel
    SessionModel,  # noqa: TC002 — SessionModel używany w Mapped[SessionModel] w relacji SQLAlchemy
)
