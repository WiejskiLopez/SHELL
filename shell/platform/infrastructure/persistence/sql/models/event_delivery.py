"""Factory for per-service inbox and outbox event models."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime
from typing import NamedTuple

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB
from shell.platform.infrastructure.persistence.sql.models.mixins.inbox_state import (
    InboxStateMixin,
)


class EventDeliveryModels(NamedTuple):
    outbox: type[DeclarativeBase]
    inbox: type[DeclarativeBase]


def build_event_delivery_models(base: type[DeclarativeBase]) -> EventDeliveryModels:
    """Build inbox and outbox ORM models bound to one BC metadata registry."""

    class OutboxEventModel(base):  # type: ignore[misc, valid-type]
        __tablename__ = "outbox_event"

        id: Mapped[str] = mapped_column(primary_key=True)
        event_type: Mapped[str] = mapped_column(nullable=False)
        occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
        payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
        correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
        causation_id: Mapped[str] = mapped_column(nullable=False, default="")
        published_at: Mapped[datetime | None] = mapped_column(
            DateTime(timezone=True), nullable=True
        )

    class InboxEventModel(InboxStateMixin, base):  # type: ignore[misc, valid-type]
        __tablename__ = "inbox_event"

        id: Mapped[str] = mapped_column(primary_key=True)
        event_type: Mapped[str] = mapped_column(nullable=False)
        occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
        payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
        correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
        causation_id: Mapped[str] = mapped_column(nullable=False, default="")
        received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    OutboxEventModel.__name__ = f"{base.__name__}OutboxEventModel"
    OutboxEventModel.__qualname__ = OutboxEventModel.__name__
    InboxEventModel.__name__ = f"{base.__name__}InboxEventModel"
    InboxEventModel.__qualname__ = InboxEventModel.__name__

    return EventDeliveryModels(outbox=OutboxEventModel, inbox=InboxEventModel)
