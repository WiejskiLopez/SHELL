from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves Mapped[...] at class definition

from sqlalchemy.orm import Mapped, mapped_column

from shell.execution_service.infrastructure.execution.persistence.sql.models.base import (
    ExecutionSqlAlchemyModelBase,
)


class UserExecutionModel(ExecutionSqlAlchemyModelBase):
    __tablename__ = "user_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    changed_at: Mapped[datetime] = mapped_column(nullable=True)
