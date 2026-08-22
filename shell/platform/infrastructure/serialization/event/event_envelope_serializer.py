from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent
from shell.platform.infrastructure.serialization.envelope.envelope_engine import EnvelopeSerializer

if TYPE_CHECKING:
    from shell.platform.infrastructure.serialization.event.domain_event_serializer import (
        DomainEventSerializer,
    )


class EventEnvelopeSerializer(EnvelopeSerializer):
    """Serializes a domain event into the outbox envelope format (event facade).

    Integration events are not handled here — they use
    :class:`IntegrationEventSerializer`, which builds a richer transport
    envelope.
    """

    def __init__(self, event_serializer: DomainEventSerializer | None = None) -> None:
        super().__init__("event_type", event_serializer)

    def to_outbox_payload(self, event: object) -> dict[str, object]:
        if not isinstance(event, DomainEvent):
            raise TypeError("EventEnvelopeSerializer requires a DomainEvent")
        return super().to_outbox_payload(event)