from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.platform.infrastructure.persistence.sql.models.base import Base
from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin


class SessionModel(Base, VersionedMixin):
    __tablename__ = "session"

    id: Mapped[str] = mapped_column(primary_key=True)
    goal: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="open")
    user_id: Mapped[str] = mapped_column(nullable=False, server_default="")
    project_id: Mapped[str] = mapped_column(nullable=False, server_default="")
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    opened_at: Mapped[datetime] = mapped_column(nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    @declared_attr  # type: ignore[arg-type]  # SQLAlchemy stubs expect Mapped[T], but __mapper_args__ returns dict
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}


__all__ = [
    "SessionModel",
]
