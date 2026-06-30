"""InboxProcessor — consumes Inbox events and triggers application logic via EventBus."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.infrastructure.platform.context import (
    causation_id_var,
    correlation_id_var,
)
from shell.infrastructure.platform.persistence.sql.models import InboxEventModel
from shell.infrastructure.platform.serialization.event_deserializer import EventDeserializer

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.application.platform.ports.ports import EventPublisher


class InboxProcessor:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        event_bus: EventPublisher,  # In-memory EventBus
        batch_size: int = 100,
    ) -> None:
        self._session_factory = session_factory
        self._event_bus = event_bus
        self._batch_size = batch_size
        self._deserializer = EventDeserializer()

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

            events_to_publish = []

            for row in rows:
                # Reconstruct full domain object from raw data
                domain_event = self._deserializer.deserialize(
                    row.event_type, row.occurred_at, row.payload
                )
                if domain_event:
                    events_to_publish.append(domain_event)

                # Mark in Inbox as processed (our ACK!)
                row.processed_at = datetime.now(tz=UTC)

            await session.commit()

            # Publish AFTER commit so Inbox events are marked processed
            # before any handler runs.  If a handler throws, the event won't
            # be lost — the commit already durable-marked it.
            if events_to_publish:
                # Restore tracing context from inbox metadata before dispatching
                for domain_event, row in zip(events_to_publish, rows, strict=False):
                    corr_token = correlation_id_var.set(row.correlation_id)
                    caus_token = causation_id_var.set(domain_event.event_id.value)
                    try:
                        await self._event_bus.publish([domain_event])
                    finally:
                        correlation_id_var.reset(corr_token)
                        causation_id_var.reset(caus_token)

            return len(rows)
