from __future__ import annotations

from datetime import datetime  # noqa: TC003 -- Mapped[datetime] requires datetime at runtime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from shell.execution.infrastructure.execution.persistence.sql.models.base import (
    ExecutionSqlAlchemyModelBase,
)
from shell.platform.infrastructure.persistence.sql.models._compat import JSONB


class SessionExecutionStateModel(ExecutionSqlAlchemyModelBase):
    __tablename__ = "session_execution_state"

    id: Mapped[str] = mapped_column(primary_key=True)
    session_execution_id: Mapped[str] = mapped_column(
        ForeignKey("session_execution.id", ondelete="CASCADE"),
        nullable=False,
    )
    direction: Mapped[str] = mapped_column(nullable=False)
    state_data: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
