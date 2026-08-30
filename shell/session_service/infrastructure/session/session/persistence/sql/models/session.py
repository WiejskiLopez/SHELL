from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves Mapped[...] at class definition

from sqlalchemy import String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin
from shell.session_service.infrastructure.session.persistence.sql.models.base import (
    SessionSqlAlchemyModelBase,
)


class SessionModel(SessionSqlAlchemyModelBase, VersionedMixin):
    __tablename__ = "session"

    id: Mapped[str] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[str] = mapped_column(nullable=False, server_default="")
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    opened_at: Mapped[datetime] = mapped_column(nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    changed_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    @declared_attr  # type: ignore[arg-type]  # SQLAlchemy stubs expect Mapped[T], but __mapper_args__ returns dict
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}


__all__ = [
    "SessionModel",
]
