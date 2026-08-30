from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves Mapped[...] at class definition

from sqlalchemy import String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin
from shell.user_service.infrastructure.user.persistence.sql.models.base import (
    UserSqlAlchemyModelBase,
)


class UserModel(UserSqlAlchemyModelBase, VersionedMixin):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    changed_at: Mapped[datetime] = mapped_column(nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}
