"""Factory for per-service inbox and outbox command models."""

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


class CommandDeliveryModels(NamedTuple):
    outbox: type[DeclarativeBase]
    inbox: type[DeclarativeBase]


def build_command_delivery_models(base: type[DeclarativeBase]) -> CommandDeliveryModels:
    """Build inbox and outbox ORM models bound to one BC metadata registry."""

    class OutboxCommandModel(DeliveryColumnsMixin, base):  # type: ignore[misc, valid-type]
        __tablename__ = "command_outbox"

        @declared_attr  # type: ignore[arg-type]
        def __table_args__(cls: type[Any]) -> tuple[object, ...]:
            return (
                UniqueConstraint("source_service", "command_id", name="uq_command_outbox_source_cmd"),
                Index("ix_command_outbox_publish", "published_at", "issued_at"),
            )

        id: Mapped[str] = mapped_column(primary_key=True)
        command_id: Mapped[str] = mapped_column(nullable=False)
        command_name: Mapped[str] = mapped_column(nullable=False)
        source_service: Mapped[str] = mapped_column(nullable=False)
        target_service: Mapped[str] = mapped_column(nullable=False)
        schema_version: Mapped[int] = mapped_column(nullable=False, default=1)
        issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
        published_at: Mapped[datetime | None] = mapped_column(
            DateTime(timezone=True), nullable=True
        )

    class InboxCommandModel(DeliveryColumnsMixin, InboxStateMixin, base):  # type: ignore[misc, valid-type]
        __tablename__ = "command_inbox"

        @declared_attr  # type: ignore[arg-type]
        def __table_args__(cls: type[Any]) -> tuple[Index | UniqueConstraint, ...]:
            return (
                UniqueConstraint(
                    "source_service",
                    "command_id",
                    name="uq_command_inbox_source_command",
                ),
                *build_inbox_state_indexes(cls.__tablename__),
            )

        id: Mapped[str] = mapped_column(primary_key=True)
        command_id: Mapped[str] = mapped_column(nullable=False)
        command_name: Mapped[str] = mapped_column(nullable=False)
        source_service: Mapped[str] = mapped_column(nullable=False)
        target_service: Mapped[str] = mapped_column(nullable=False)
        schema_version: Mapped[int] = mapped_column(nullable=False, default=1)
        issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
        received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    OutboxCommandModel.__name__ = f"{base.__name__}OutboxCommandModel"
    OutboxCommandModel.__qualname__ = OutboxCommandModel.__name__
    InboxCommandModel.__name__ = f"{base.__name__}InboxCommandModel"
    InboxCommandModel.__qualname__ = InboxCommandModel.__name__

    return CommandDeliveryModels(outbox=OutboxCommandModel, inbox=InboxCommandModel)