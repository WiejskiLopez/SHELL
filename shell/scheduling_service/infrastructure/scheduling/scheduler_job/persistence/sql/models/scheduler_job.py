from __future__ import annotations

from datetime import datetime  # noqa: TC003 -- potrzebny w runtime dla Mapped[datetime]

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB
from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin
from shell.scheduling_service.infrastructure.scheduling.persistence.sql.models.base import (
    SchedulingSqlAlchemyModelBase,
)


class SchedulerJobModel(SchedulingSqlAlchemyModelBase, VersionedMixin):
    __tablename__ = "scheduler_job"

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
    config: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    changed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}
