from __future__ import annotations

from shell.platform.infrastructure.serialization.payload.payload_object_serializer import (
    PayloadObjectSerializer,
)


class DomainEventSerializer(PayloadObjectSerializer):
    """Serializes a domain event into its transport payload."""
