from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.platform.context import get_causation_id, get_correlation_id
from shell.infrastructure.platform.messaging.memory_outbox_store.outbox_record import OutboxRecord
from shell.infrastructure.platform.serialization import DomainEventSerializer

if TYPE_CHECKING:
    from shell.domain.platform.events import DomainEvent


class InMemoryOutboxStore:
    """Simple in-memory outbox for tests — implements the same interface as SqlOutboxPublisher."""

    def __init__(self) -> None:
        self.records: list[OutboxRecord] = []

    async def publish(self, events: list[DomainEvent]) -> None:
        import uuid

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
                        occurred_at=event.occurred_at,
                        payload=payload,
                        correlation_id=correlation_id,
                        causation_id=causation_id,
                    )
                )
            except Exception:
                import logging

                logging.getLogger(__name__).exception(
                    "Failed to serialize event %s", type(event).__name__
                )
                continue

    def pending(self) -> list[OutboxRecord]:
        return [record for record in self.records if not record.is_published]
