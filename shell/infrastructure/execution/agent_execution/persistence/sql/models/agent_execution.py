from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column

from shell.infrastructure.platform.persistence.sql.models.base import Base

if TYPE_CHECKING:
    from datetime import datetime



class AgentExecutionModel(Base):
    __tablename__ = "agent_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    node_execution_id: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
