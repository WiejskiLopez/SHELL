from __future__ import annotations

from datetime import datetime  # noqa: TC003 -- Mapped[datetime] requires datetime at runtime

from sqlalchemy.orm import Mapped, mapped_column

from shell.infrastructure.platform.persistence.sql.models.base import Base


class SessionExecutionModel(Base):
    __tablename__ = "session_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    user_execution_id: Mapped[str | None] = mapped_column(nullable=True)
    session_id: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
