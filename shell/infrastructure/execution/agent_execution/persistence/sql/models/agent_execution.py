from __future__ import annotations

from datetime import datetime  # noqa: TC003 — runtime dla SQLAlchemy Mapped

from sqlalchemy.orm import Mapped, mapped_column

from shell.platform.infrastructure.persistence.sql.models.base import Base


class AgentExecutionModel(Base):
    __tablename__ = "agent_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    node_execution_id: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
