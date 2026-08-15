from __future__ import annotations

from datetime import datetime  # noqa: TC003 — runtime dla SQLAlchemy Mapped

from sqlalchemy.orm import Mapped, mapped_column

from shell.execution_service.infrastructure.execution.persistence.sql.models.base import (
    ExecutionSqlAlchemyModelBase,
)
from shell.platform.infrastructure.persistence.sql.models._compat import JSONB


class AgentSkillExecutionModel(ExecutionSqlAlchemyModelBase):
    __tablename__ = "agent_skill_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    agent_execution_id: Mapped[str] = mapped_column(nullable=False)
    skill_data: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
