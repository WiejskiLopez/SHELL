from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column

from shell.platform.infrastructure.persistence.sql.models.base import Base

if TYPE_CHECKING:
    from datetime import datetime



class AgentConfigExecutionModel(Base):
    __tablename__ = "agent_config_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    agent_execution_id: Mapped[str] = mapped_column(nullable=False)
    session_execution_id: Mapped[str | None] = mapped_column(nullable=True)
    user_execution_id: Mapped[str | None] = mapped_column(nullable=True)
    model: Mapped[str] = mapped_column(nullable=False, default="")
    temperature: Mapped[float] = mapped_column(nullable=False, default=0.0)
    max_tokens: Mapped[int] = mapped_column(nullable=False, default=0)
    top_p: Mapped[float] = mapped_column(nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
