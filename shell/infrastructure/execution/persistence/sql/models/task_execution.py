from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from shell.infrastructure.platform.persistence.sql.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column


class TaskExecutionModel(Base):
    __tablename__ = "task_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(nullable=False, default="created")
    name: Mapped[str] = mapped_column(nullable=False)
    work_dir: Mapped[str] = mapped_column(nullable=False, default="")
    workflow_id: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
