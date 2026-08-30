from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves Mapped[...] at class definition

from sqlalchemy import String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin
from shell.user_service.infrastructure.user.persistence.sql.models.base import (
    UserSqlAlchemyModelBase,
)


class AuthSessionModel(UserSqlAlchemyModelBase, VersionedMixin):
    __tablename__ = "auth_sessions"

    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    changed_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}
