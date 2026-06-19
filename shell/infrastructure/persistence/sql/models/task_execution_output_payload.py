from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TaskExecutionOutputPayloadModel(Base):
    __tablename__ = "task_execution_output_payload"

    id: Mapped[str] = mapped_column(primary_key=True)
    task_execution_id: Mapped[str] = mapped_column(
        ForeignKey("task_execution.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
