from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class SessionModel(Base, VersionedMixin):
    __tablename__ = "session"

    id: Mapped[str] = mapped_column(primary_key=True)
    goal: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="open")
    user_id: Mapped[str] = mapped_column(nullable=False, server_default="")
    project_id: Mapped[str] = mapped_column(nullable=False, server_default="")
    environment_os: Mapped[str] = mapped_column(nullable=False, server_default="")
    environment_runtime: Mapped[str] = mapped_column(nullable=False, server_default="")
    environment_cwd: Mapped[str] = mapped_column(nullable=False, server_default="")
    opened_at: Mapped[datetime] = mapped_column(nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict:
        return {"version_id_col": cls.version}


__all__ = [
    "SessionModel",
]
