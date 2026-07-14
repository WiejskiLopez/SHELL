"""InboxProcessor — consumes Inbox events and triggers application logic via EventBus."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.platform.infrastructure.context import (
    causation_id_var,
    correlation_id_var,
)
from shell.platform.infrastructure.persistence.sql.models import InboxEventModel
from shell.platform.infrastructure.serialization.event_deserializer import EventDeserializer

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.application.ports.ports import EventPublisher
    from shell.platform.domain.events import DomainEvent


class InboxProcessor:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        event_bus: EventPublisher,  # In-memory EventBus
        batch_size: int = 100,
        registry: dict[str, type[DomainEvent]] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._event_bus = event_bus
        self._batch_size = batch_size
        self._deserializer = EventDeserializer(registry=registry)  # type: ignore[arg-type]

        engine = getattr(session_factory, "bind", None)
        dialect_name: str = engine.dialect.name if engine is not None else "unknown"
        self._skip_locked: bool = dialect_name not in ("sqlite",)

    async def run_once(self) -> int:
        async with self._session_factory() as session:
            stmt = (
                select(InboxEventModel)
                .where(InboxEventModel.processed_at.is_(None))
                .order_by(InboxEventModel.received_at)
                .limit(self._batch_size)
            )
            if self._skip_locked:
                stmt = stmt.with_for_update(skip_locked=True)

            rows = (await session.execute(stmt)).scalars().all()
            if not rows:
                return 0

            # Pair succesfully deserialized events with their rows
            pairs: list[tuple[DomainEvent, InboxEventModel]] = []

            for row in rows:
                # Reconstruct full domain object from raw data
                domain_event = self._deserializer.deserialize(
                    row.event_type, row.occurred_at, row.payload
                )
                if domain_event:
                    pairs.append((domain_event, row))

                # Mark in Inbox as processed (our ACK!)
                row.processed_at = datetime.now(tz=UTC)

            await session.commit()

            # Publish AFTER commit so Inbox events are marked processed
            # before any handler runs.  If a handler throws, the event won't
            # be lost — the commit already durable-marked it.
            if pairs:
                # Restore tracing context from inbox metadata before dispatching
                for domain_event, row in pairs:
                    corr_token = correlation_id_var.set(row.correlation_id)
                    caus_token = causation_id_var.set(domain_event.event_id.value)
                    try:
                        await self._event_bus.publish([domain_event])
                    finally:
                        correlation_id_var.reset(corr_token)
                        causation_id_var.reset(caus_token)

            return len(rows)
