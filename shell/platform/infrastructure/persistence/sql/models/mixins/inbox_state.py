"""InboxStateMixin — shared operational state columns for every inbox delivery model.

Event, message and command inboxes share the same operational lifecycle so the
columns live in one platform mixin instead of being duplicated across models.
"""

from __future__ import annotations

from datetime import UTC, datetime  # noqa: TC003 — Mapped[datetime] requires runtime type
from typing import Any

from sqlalchemy import DateTime, Index
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.platform.domain.value_objects.inbox_status import InboxStatus


def _default_next_attempt_at() -> datetime:
    return datetime.now(tz=UTC).replace(microsecond=0)


def build_inbox_state_indexes(table_name: str) -> tuple[Index, ...]:
    """Return the shared operational indexes for an inbox table."""
    return (
        Index(
            f"ix_{table_name}_status_next_attempt_received",
            "status",
            "next_attempt_at",
            "received_at",
        ),
        Index(f"ix_{table_name}_status_lease_until", "status", "lease_until"),
    )


class InboxStateMixin:
    """Adds the shared operational lifecycle columns to an inbox model.

    The ``status`` column uses ``PENDING`` as its default so every inbox row
    starts in the same explicit state. ``next_attempt_at`` defaults to the insert
    time (``received_at`` is equivalent at insert time) so the claim query never
    has to special-case NULL.
    """

    @declared_attr  # type: ignore[arg-type]  # SQLAlchemy stubs expect Mapped[T]; __table_args__ returns tuple of Index
    def __table_args__(cls: type[Any]) -> tuple[Index, ...]:
        return build_inbox_state_indexes(cls.__tablename__)

    status: Mapped[str] = mapped_column(nullable=False, default=InboxStatus.PENDING.value)
    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_default_next_attempt_at
    )
    lease_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    claimed_by: Mapped[str | None] = mapped_column(nullable=True, default=None)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    failed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    last_attempted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(nullable=True, default=None)
    error_code: Mapped[str | None] = mapped_column(nullable=True, default=None)
    error_message: Mapped[str | None] = mapped_column(nullable=True, default=None)
    schema_version: Mapped[int] = mapped_column(nullable=False, default=1)
