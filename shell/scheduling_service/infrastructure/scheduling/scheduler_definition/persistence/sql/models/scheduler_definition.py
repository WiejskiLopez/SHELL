from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves Mapped[...] at class definition

from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB
from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin
from shell.scheduling_service.infrastructure.scheduling.persistence.sql.models.base import (
    SchedulingSqlAlchemyModelBase,
)


class SchedulerDefinitionModel(SchedulingSqlAlchemyModelBase, VersionedMixin):
    __tablename__ = "scheduler_definition"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    source_context: Mapped[str] = mapped_column(nullable=False)
    trigger_event_type: Mapped[str] = mapped_column(nullable=False)
    trigger_filter: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    action_type: Mapped[str] = mapped_column(nullable=False)
    action_config: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    execution_policy: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    changed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    @declared_attr  # type: ignore[arg-type]  # SQLAlchemy stubs expect Mapped[T], but __mapper_args__ returns dict
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}
