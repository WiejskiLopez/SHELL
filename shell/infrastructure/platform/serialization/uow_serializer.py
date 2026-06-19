from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.platform.serialization.event_serializer import DomainEventSerializer

if TYPE_CHECKING:
    from shell.domain.platform.events import DomainEvent


def serialize_staged_events(events: list[DomainEvent]) -> list[dict[str, object]]:
    serializer = DomainEventSerializer()
    return [serializer.to_outbox_payload(event) for event in events]
