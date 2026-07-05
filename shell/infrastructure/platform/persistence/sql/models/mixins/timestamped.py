"""TimestampedMixin — adds created_at, updated_at, deleted_at columns."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 — SQLAlchemy Mapped[datetime] needs runtime access

from sqlalchemy.orm import Mapped, mapped_column


class TimestampedMixin:
    """Adds created_at, updated_at, deleted_at timestamp columns.

    Models that already define their own ``created_at`` should add
    the missing ``updated_at`` and ``deleted_at`` columns manually
    instead of inheriting this mixin (SQLAlchemy does not allow
    overriding columns from mixins).
    """

    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
