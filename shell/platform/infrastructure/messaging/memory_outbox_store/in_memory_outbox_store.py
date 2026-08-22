from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from shell.platform.infrastructure.context import get_causation_id, get_correlation_id
from shell.platform.infrastructure.messaging.memory_outbox_store.outbox_record import OutboxRecord
from shell.platform.infrastructure.serialization import DomainEventSerializer

if TYPE_CHECKING:
    from shell.platform.application.ports.technical_id_generator import TechnicalIdGenerator
    from shell.platform.domain.events import DomainEvent


class InMemoryOutboxStore:
    """Simple in-memory outbox double for domain-event unit tests."""

    def __init__(self, id_generator: TechnicalIdGenerator | None = None) -> None:
        self.records: list[OutboxRecord] = []
        from shell.platform.infrastructure.identity.uuid_technical_id_generator import (
            UuidTechnicalIdGenerator,
        )

        self._id_generator = id_generator or UuidTechnicalIdGenerator()

    async def publish(self, events: list[DomainEvent]) -> None:
        correlation_id = get_correlation_id()
        causation_id = get_causation_id()
        serializer = DomainEventSerializer()
        for event in events:
            try:
                payload = serializer.to_payload(event)
                self.records.append(
                    OutboxRecord(
                        id=self._id_generator.new_id(),
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
