from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from shell.platform.infrastructure.context import get_causation_id, get_correlation_id
from shell.platform.infrastructure.messaging.memory_outbox_store.outbox_record import OutboxRecord
from shell.platform.infrastructure.serialization import DomainEventSerializer

if TYPE_CHECKING:
    from shell.platform.domain.events import DomainEvent


class InMemoryOutboxStore:
    """Simple in-memory outbox for tests — implements the same interface as SqlOutboxPublisher."""

    def __init__(self) -> None:
        self.records: list[OutboxRecord] = []

    async def publish(self, events: list[DomainEvent]) -> None:
        correlation_id = get_correlation_id()
        causation_id = get_causation_id()
        serializer = DomainEventSerializer()
        for event in events:
            try:
                payload = serializer.to_payload(event)
                self.records.append(
                    OutboxRecord(
                        id=str(uuid.uuid4()),
                        event_type=type(event).__name__,
                        occurred_at=event.occurred_at.value,
                        payload=payload,
                        correlation_id=correlation_id,
                        causation_id=causation_id,
                    )
                )
            except Exception:
                logging.getLogger(__name__).critical(
                    "Failed to serialize event %s — event LOST", type(event).__name__
                )
                raise

    def pending(self) -> list[OutboxRecord]:
        return [record for record in self.records if not record.is_published]
