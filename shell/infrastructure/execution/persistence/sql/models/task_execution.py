from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from shell.infrastructure.platform.persistence.sql.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class TaskExecutionModel(Base):
    __tablename__ = "task_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    parent_task_execution_id: Mapped[str | None] = mapped_column(
        ForeignKey("task_execution.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(nullable=False, default="CREATED")
    name: Mapped[str] = mapped_column(nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    hash: Mapped[str] = mapped_column(nullable=False)
    body: Mapped[str] = mapped_column(nullable=False, default="")
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)
    work_dir: Mapped[str] = mapped_column(nullable=False, default="")
    workflow_id: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
