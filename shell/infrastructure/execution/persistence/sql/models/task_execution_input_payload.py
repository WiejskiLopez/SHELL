from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from shell.infrastructure.platform.persistence.sql.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class TaskExecutionInputPayloadModel(Base):
    __tablename__ = "task_execution_input_payload"

    id: Mapped[str] = mapped_column(primary_key=True)
    task_execution_id: Mapped[str] = mapped_column(
        ForeignKey("task_execution.id", ondelete="CASCADE"),
        nullable=False,
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
