from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TaskExecutionModel(Base):
    __tablename__ = "task_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    parent_task_execution_id: Mapped[str | None] = mapped_column(
        ForeignKey("task_execution.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(nullable=False, default="PENDING")
    name: Mapped[str] = mapped_column(nullable=False, index=True)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    hash: Mapped[str] = mapped_column(nullable=False)
    body: Mapped[str] = mapped_column(nullable=False, default="")
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
