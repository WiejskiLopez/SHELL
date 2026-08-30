from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves Mapped[...] at class definition

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from shell.execution_service.infrastructure.execution.persistence.sql.models.base import (
    ExecutionSqlAlchemyModelBase,
)
from shell.platform.infrastructure.persistence.sql.models._compat import JSONB


class NodeExecutionStateModel(ExecutionSqlAlchemyModelBase):
    __tablename__ = "node_execution_state"

    id: Mapped[str] = mapped_column(primary_key=True)
    node_execution_id: Mapped[str] = mapped_column(
        ForeignKey("node_execution.id", ondelete="CASCADE"),
        nullable=False,
    )
    direction: Mapped[str] = mapped_column(nullable=False)
    state_data: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
