from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin
from shell.infrastructure.scheduling.persistence.sql.models._compat import JSONB
from shell.infrastructure.scheduling.persistence.sql.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class SchedulerExecutionModel(Base, VersionedMixin):
    __tablename__ = "scheduler_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    scheduler_definition_id: Mapped[str] = mapped_column(
        ForeignKey("scheduler_definition.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(nullable=False, default="")
    job_type: Mapped[str] = mapped_column(nullable=False, default="messaging")
    interval_seconds: Mapped[float] = mapped_column(nullable=False, default=1.0)
    batch_size: Mapped[int] = mapped_column(nullable=False, default=50)
    enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict:
        return {"version_id_col": cls.version}
