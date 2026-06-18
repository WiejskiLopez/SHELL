from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from shell.infrastructure.messaging.memory_outbox_store.outbox_record import OutboxRecord

if TYPE_CHECKING:
    from shell.domain.events.events import DomainEvent


class InMemoryOutboxStore:
    """Simple in-memory outbox for tests — implements the same interface as SqlOutboxPublisher."""

    def __init__(self) -> None:
        self.records: list[OutboxRecord] = []

    async def publish(self, events: list[DomainEvent]) -> None:
        import uuid

        for event in events:
            payload = {
                field.name: str(getattr(event, field.name))
                for field in dataclasses.fields(event)  # type: ignore[arg-type]
                if field.name != "occurred_at"
            }
            self.records.append(
                OutboxRecord(
                    id=str(uuid.uuid4()),
                    event_type=type(event).__name__,
                    occurred_at=event.occurred_at,
                    payload=payload,
                )
            )

    def pending(self) -> list[OutboxRecord]:
        return [record for record in self.records if not record.is_published]
