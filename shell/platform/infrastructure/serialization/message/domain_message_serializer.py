from __future__ import annotations

from shell.platform.infrastructure.serialization.payload.payload_object_serializer import (
    PayloadObjectSerializer,
)


class DomainMessageSerializer(PayloadObjectSerializer):
    """Serializes a domain message into its transport payload (message facade)."""