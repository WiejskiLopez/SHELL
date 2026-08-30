from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves Mapped[...] at class definition

from sqlalchemy.orm import Mapped, mapped_column

from shell.execution_service.infrastructure.execution.persistence.sql.models.base import (
    ExecutionSqlAlchemyModelBase,
)


class AgentConfigExecutionModel(ExecutionSqlAlchemyModelBase):
    __tablename__ = "agent_config_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    agent_execution_id: Mapped[str] = mapped_column(nullable=False)
    config_data: Mapped[str] = mapped_column(nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    changed_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
