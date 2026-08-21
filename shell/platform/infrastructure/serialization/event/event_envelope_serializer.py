from __future__ import annotations

from shell.platform.infrastructure.serialization.event.domain_event_serializer import (
    DomainEventSerializer,
)
from shell.platform.infrastructure.serialization.envelope.envelope_engine import EnvelopeSerializer


class EventEnvelopeSerializer(EnvelopeSerializer):
    """Serializes a domain event into the outbox envelope format (event facade)."""

    def __init__(self, event_serializer: DomainEventSerializer | None = None) -> None:
        super().__init__("event_type", event_serializer)