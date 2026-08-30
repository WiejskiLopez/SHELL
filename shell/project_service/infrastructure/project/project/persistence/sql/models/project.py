from __future__ import annotations

from datetime import datetime  # noqa: TC003 -- SQLAlchemy model uses datetime for column definition

from sqlalchemy import String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin
from shell.project_service.infrastructure.project.persistence.sql.models.base import (
    ProjectSqlAlchemyModelBase,
)


class ProjectModel(ProjectSqlAlchemyModelBase, VersionedMixin):
    __tablename__ = "project"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    repo_url: Mapped[str | None] = mapped_column(nullable=True, default=None)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    changed_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}
