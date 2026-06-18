"""InMemoryOutboxStore — in-process store for unit-testing the outbox pattern."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.events.events import DomainEvent


@dataclass
class OutboxRecord:
    id: str
    event_type: str
    occurred_at: datetime
    payload: dict  # type: ignore[type-arg]
    published_at: datetime | None = None

    @property
    def is_published(self) -> bool:
        return self.published_at is not None


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
