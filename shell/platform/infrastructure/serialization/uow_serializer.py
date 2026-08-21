from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.infrastructure.serialization.event.event_envelope_serializer import (
    EventEnvelopeSerializer,
)

if TYPE_CHECKING:
    from shell.platform.domain.events import DomainEvent


def serialize_staged_events(events: list[DomainEvent]) -> list[dict[str, object]]:
    serializer = EventEnvelopeSerializer()
    return [serializer.to_outbox_payload(event) for event in events]
