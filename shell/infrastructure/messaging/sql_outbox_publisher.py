"""SqlOutboxPublisher — EventPublisher adapter that writes to outbox_event table.

Events are stored in a dedicated DB session so they survive even if the caller's
transaction was already committed.  An OutboxToInboxRelay then reads them and fans them
out to the EventBus.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from shell.infrastructure.persistence.sql.models import OutboxEventModel
from shell.shared.serialization import DomainEventSerializer

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.domain.events.events import DomainEvent


class SqlOutboxPublisher:
    """Writes domain events to the ``outbox_event`` table (own session per call)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def publish(self, events: Sequence[DomainEvent]) -> None:
        if not events:
            return
        serializer = DomainEventSerializer()
        async with self._session_factory() as session:
            for event in events:
                try:
                    payload = serializer.to_payload(event)
                    session.add(
                        OutboxEventModel(
                            id=str(uuid.uuid4()),
                            event_type=type(event).__name__,
                            occurred_at=event.occurred_at,
                            payload=payload,
                            published_at=None,
                        )
                    )
                except Exception:
                    import logging

                    logging.getLogger(__name__).exception(
                        "Failed to serialize event %s", type(event).__name__
                    )
                    continue
            await session.commit()
