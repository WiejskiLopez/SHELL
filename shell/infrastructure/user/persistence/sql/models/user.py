from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] requires datetime at runtime

from sqlalchemy.orm import Mapped, mapped_column

from shell.infrastructure.platform.persistence.sql.models.base import Base


class UserModel(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
