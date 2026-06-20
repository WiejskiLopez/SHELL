from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from shell.infrastructure.scheduling.persistence.sql.models._compat import JSONB
from shell.infrastructure.scheduling.persistence.sql.models.base import Base


class SchedulerDefinitionModel(Base):
    __tablename__ = "scheduler_definition"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    source_context: Mapped[str] = mapped_column(nullable=False)
    trigger_event_type: Mapped[str] = mapped_column(nullable=False)
    trigger_filter: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    action_type: Mapped[str] = mapped_column(nullable=False)
    action_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    execution_policy: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)
