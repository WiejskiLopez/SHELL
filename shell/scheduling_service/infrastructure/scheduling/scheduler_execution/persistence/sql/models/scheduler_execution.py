from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB
from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin
from shell.scheduling_service.infrastructure.scheduling.persistence.sql.models.base import (
    SchedulingSqlAlchemyModelBase,
)


class SchedulerExecutionModel(SchedulingSqlAlchemyModelBase, VersionedMixin):
    __tablename__ = "scheduler_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    scheduler_definition_id: Mapped[str] = mapped_column(
        ForeignKey("scheduler_definition.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_event_id: Mapped[str | None] = mapped_column(nullable=True)
    trigger_event_type: Mapped[str | None] = mapped_column(nullable=True)
    action_ref: Mapped[str | None] = mapped_column(nullable=True)
    action_ref_type: Mapped[str | None] = mapped_column(nullable=True)
    input_state: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    output_state: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(nullable=True)

    @declared_attr  # type: ignore[arg-type]  # SQLAlchemy stubs expect Mapped[T], but __mapper_args__ returns dict
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}
