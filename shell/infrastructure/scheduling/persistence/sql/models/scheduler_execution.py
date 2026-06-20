from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from shell.infrastructure.scheduling.persistence.sql.models._compat import JSONB
from shell.infrastructure.scheduling.persistence.sql.models.base import Base


class SchedulerExecutionModel(Base):
    __tablename__ = "scheduler_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    scheduler_definition_id: Mapped[str] = mapped_column(
        ForeignKey("scheduler_definition.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(nullable=False, default="pending")
    trigger_event_id: Mapped[str | None] = mapped_column(nullable=True)
    trigger_event_type: Mapped[str | None] = mapped_column(nullable=True)
    action_ref: Mapped[str | None] = mapped_column(nullable=True)
    action_ref_type: Mapped[str | None] = mapped_column(nullable=True)
    input_state: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    output_state: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)
