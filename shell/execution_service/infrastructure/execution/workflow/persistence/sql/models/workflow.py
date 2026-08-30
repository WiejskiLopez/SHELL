from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves Mapped[...] at class definition

from sqlalchemy import String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.execution_service.infrastructure.execution.persistence.sql.models.base import (
    ExecutionSqlAlchemyModelBase,
)
from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin


class WorkflowModel(ExecutionSqlAlchemyModelBase, VersionedMixin):
    __tablename__ = "workflow"

    id: Mapped[str] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    session_id: Mapped[str] = mapped_column(nullable=False)
    project_id: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    changed_at: Mapped[datetime] = mapped_column(nullable=True)

    @declared_attr  # type: ignore[arg-type]  # SQLAlchemy stubs expect Mapped[T], but __mapper_args__ returns dict
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}
