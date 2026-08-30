"""Factory for the ``processed_delivery`` deduplication model.

The dedup table is the explicit fallback (ref2.md §4.1) for handlers that
cannot share the processor's transaction: a handler writes a row atomically
with its own business change, and the processor consults it before dispatch so
an at-least-once redelivery is never executed twice.

Uniqueness is ``(consumer_name, outbox_id)`` — the same outbox record replayed by
the same consumer is always a no-op.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves Mapped[...] at class definition

from sqlalchemy import DateTime, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB


def build_processed_delivery_model(base: type[DeclarativeBase]) -> type[DeclarativeBase]:
    """Build the ``processed_delivery`` ORM model bound to one BC metadata registry."""

    class ProcessedDeliveryModel(base):  # type: ignore[misc, valid-type]
        __tablename__ = "processed_delivery"
        __table_args__ = (
            UniqueConstraint(
                "consumer_name",
                "outbox_id",
                name="uq_processed_delivery_consumer_outbox",
            ),
        )

        id: Mapped[str] = mapped_column(primary_key=True)
        consumer_name: Mapped[str] = mapped_column(nullable=False)
        outbox_id: Mapped[str] = mapped_column(nullable=False)
        payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
        processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    ProcessedDeliveryModel.__name__ = f"{base.__name__}ProcessedDeliveryModel"
    ProcessedDeliveryModel.__qualname__ = ProcessedDeliveryModel.__name__

    return ProcessedDeliveryModel
