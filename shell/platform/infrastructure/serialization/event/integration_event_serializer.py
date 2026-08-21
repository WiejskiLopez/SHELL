from __future__ import annotations

from shell.platform.application.events import IntegrationEvent
from shell.platform.infrastructure.serialization.payload.payload_object_serializer import (
    PayloadObjectSerializer,
)


class IntegrationEventSerializer(PayloadObjectSerializer):
    """Serializes integration events at the transport boundary."""

    def to_payload(self, event: object) -> dict[str, object]:
        if not isinstance(event, IntegrationEvent):
            raise TypeError("IntegrationEventSerializer requires an IntegrationEvent")
        return super().to_payload(event)
