from __future__ import annotations

from shell.platform.infrastructure.serialization.message.domain_message_serializer import (
    DomainMessageSerializer,
)
from shell.platform.infrastructure.serialization.envelope.envelope_engine import EnvelopeSerializer


class MessageEnvelopeSerializer(EnvelopeSerializer):
    """Serializes a domain message into the outbox envelope format (message facade)."""

    def __init__(self, message_serializer: DomainMessageSerializer | None = None) -> None:
        super().__init__("message_type", message_serializer)