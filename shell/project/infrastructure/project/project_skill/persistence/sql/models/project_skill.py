from __future__ import annotations

from datetime import datetime  # noqa: TC003 -- SQLAlchemy model uses datetime for column definition

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB
from shell.project.infrastructure.project.persistence.sql.models.base import (
    ProjectSqlAlchemyModelBase,
)


class ProjectSkillModel(ProjectSqlAlchemyModelBase):
    __tablename__ = "project_skill"

    id: Mapped[str] = mapped_column(primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_data: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
