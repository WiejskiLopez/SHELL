"""Factory for per-service inbox and outbox command models."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves Mapped[...] at class definition
from typing import NamedTuple

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB
from shell.platform.infrastructure.persistence.sql.models.mixins.inbox_state import (
    InboxStateMixin,
)


class CommandDeliveryModels(NamedTuple):
    outbox: type[DeclarativeBase]
    inbox: type[DeclarativeBase]


def build_command_delivery_models(base: type[DeclarativeBase]) -> CommandDeliveryModels:
    """Build inbox and outbox ORM models bound to one BC metadata registry."""

    class OutboxCommandModel(base):  # type: ignore[misc, valid-type]
        __tablename__ = "outbox_command"

        id: Mapped[str] = mapped_column(primary_key=True)
        command_type: Mapped[str] = mapped_column(nullable=False)
        occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
        payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
        correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
        causation_id: Mapped[str] = mapped_column(nullable=False, default="")
        published_at: Mapped[datetime | None] = mapped_column(
            DateTime(timezone=True), nullable=True
        )

    class InboxCommandModel(InboxStateMixin, base):  # type: ignore[misc, valid-type]
        __tablename__ = "inbox_command"

        id: Mapped[str] = mapped_column(primary_key=True)
        outbox_id: Mapped[str] = mapped_column(nullable=False, unique=True)
        command_type: Mapped[str] = mapped_column(nullable=False)
        occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
        payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
        correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
        causation_id: Mapped[str] = mapped_column(nullable=False, default="")
        received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    OutboxCommandModel.__name__ = f"{base.__name__}OutboxCommandModel"
    OutboxCommandModel.__qualname__ = OutboxCommandModel.__name__
    InboxCommandModel.__name__ = f"{base.__name__}InboxCommandModel"
    InboxCommandModel.__qualname__ = InboxCommandModel.__name__

    return CommandDeliveryModels(outbox=OutboxCommandModel, inbox=InboxCommandModel)
