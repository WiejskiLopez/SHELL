from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class WorkflowModel(Base, VersionedMixin):
    __tablename__ = "workflow"

    id: Mapped[str] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(nullable=False, default="idle")
    session_execution_id: Mapped[str | None] = mapped_column(nullable=True)
    session_id: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict:
        return {"version_id_col": cls.version}
