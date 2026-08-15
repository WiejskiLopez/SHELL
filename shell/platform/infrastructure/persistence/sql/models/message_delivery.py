"""Factory for per-service inbox and outbox message models."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 -- Mapped[datetime] requires runtime type
from typing import Any, NamedTuple

from sqlalchemy import DateTime, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB
from shell.platform.infrastructure.persistence.sql.models.mixins.inbox_state import (
    InboxStateMixin,
    build_inbox_state_indexes,
)


class MessageDeliveryModels(NamedTuple):
    outbox: type[DeclarativeBase]
    inbox: type[DeclarativeBase]


def build_message_delivery_models(base: type[DeclarativeBase]) -> MessageDeliveryModels:
    """Build inbox and outbox ORM models bound to one BC metadata registry."""

    class OutboxMessageModel(base):  # type: ignore[misc, valid-type]
        __tablename__ = "outbox_message"

        __table_args__ = (Index("ix_outbox_message_published_at", "published_at"),)

        id: Mapped[str] = mapped_column(primary_key=True)
        message_type: Mapped[str] = mapped_column(nullable=False)
        occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
        payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
        correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
        causation_id: Mapped[str] = mapped_column(nullable=False, default="")
        published_at: Mapped[datetime | None] = mapped_column(
            DateTime(timezone=True), nullable=True
        )

    class InboxMessageModel(InboxStateMixin, base):  # type: ignore[misc, valid-type]
        __tablename__ = "inbox_message"

        @declared_attr  # type: ignore[arg-type]  # SQLAlchemy stubs expect Mapped[T]; __table_args__ returns tuple of Index
        def __table_args__(cls: type[Any]) -> tuple[Index, ...]:
            return (
                Index("ix_inbox_message_processed_at", "processed_at"),
                *build_inbox_state_indexes(cls.__tablename__),
            )

        id: Mapped[str] = mapped_column(primary_key=True)
        message_type: Mapped[str] = mapped_column(nullable=False)
        occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
        payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
        correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
        causation_id: Mapped[str] = mapped_column(nullable=False, default="")
        received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    OutboxMessageModel.__name__ = f"{base.__name__}OutboxMessageModel"
    OutboxMessageModel.__qualname__ = OutboxMessageModel.__name__
    InboxMessageModel.__name__ = f"{base.__name__}InboxMessageModel"
    InboxMessageModel.__qualname__ = InboxMessageModel.__name__

    return MessageDeliveryModels(outbox=OutboxMessageModel, inbox=InboxMessageModel)
