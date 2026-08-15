from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] requires datetime at runtime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shell.user_service.infrastructure.user.persistence.sql.models.base import (
    UserSqlAlchemyModelBase,
)


class AuthSessionModel(UserSqlAlchemyModelBase):
    __tablename__ = "auth_sessions"

    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    changed_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
