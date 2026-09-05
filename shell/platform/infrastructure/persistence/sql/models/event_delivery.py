"""Factory for per-service inbox and outbox event models."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves Mapped[...] at class definition
from typing import Any, NamedTuple

from sqlalchemy import DateTime, Index, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from shell.platform.infrastructure.messaging.delivery.delivery_columns import (
    DeliveryColumnsMixin,
)
from shell.platform.infrastructure.persistence.sql.models.mixins.inbox_state import (
    InboxStateMixin,
    build_inbox_state_indexes,
)


class EventDeliveryModels(NamedTuple):
    outbox: type[DeclarativeBase]
    inbox: type[DeclarativeBase]


def build_event_delivery_models(base: type[DeclarativeBase]) -> EventDeliveryModels:
    """Build inbox and outbox ORM models bound to one BC metadata registry."""

    class OutboxEventModel(DeliveryColumnsMixin, base):  # type: ignore[misc, valid-type]
        __tablename__ = "event_outbox"

        @declared_attr  # type: ignore[arg-type]
        def __table_args__(cls: type[Any]) -> tuple[Index | UniqueConstraint, ...]:
            return (
                UniqueConstraint("event_id", name="uq_event_outbox_event_id"),
                Index("ix_event_outbox_publish", "published_at", "occurred_at"),
            )

        id: Mapped[str] = mapped_column(primary_key=True)
        event_id: Mapped[str] = mapped_column(nullable=False)
        source_service: Mapped[str] = mapped_column(nullable=False)
        integration_event_name: Mapped[str] = mapped_column(nullable=False)
        occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
        aggregate_id: Mapped[str] = mapped_column(nullable=False)
        schema_version: Mapped[int] = mapped_column(nullable=False, default=1)
        published_at: Mapped[datetime | None] = mapped_column(
            DateTime(timezone=True), nullable=True
        )

    class InboxEventModel(DeliveryColumnsMixin, InboxStateMixin, base):  # type: ignore[misc, valid-type]
        __tablename__ = "event_inbox"

        @declared_attr  # type: ignore[arg-type]
        def __table_args__(cls: type[Any]) -> tuple[Index | UniqueConstraint, ...]:
            return (
                UniqueConstraint(
                    "source_service",
                    "event_id",
                    name="uq_event_inbox_source_event",
                ),
                *build_inbox_state_indexes(cls.__tablename__),
            )

        id: Mapped[str] = mapped_column(primary_key=True)
        event_id: Mapped[str] = mapped_column(nullable=False)
        source_service: Mapped[str] = mapped_column(nullable=False)
        integration_event_name: Mapped[str] = mapped_column(nullable=False)
        occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
        aggregate_id: Mapped[str] = mapped_column(nullable=False)
        received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    OutboxEventModel.__name__ = f"{base.__name__}OutboxEventModel"
    OutboxEventModel.__qualname__ = OutboxEventModel.__name__
    InboxEventModel.__name__ = f"{base.__name__}InboxEventModel"
    InboxEventModel.__qualname__ = InboxEventModel.__name__

    return EventDeliveryModels(outbox=OutboxEventModel, inbox=InboxEventModel)
