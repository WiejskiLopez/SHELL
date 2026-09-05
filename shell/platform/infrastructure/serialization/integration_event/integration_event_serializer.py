from __future__ import annotations

from shell.platform.application.events import IntegrationEvent
from shell.platform.infrastructure.serialization.payload.payload_object_serializer import (
    PayloadObjectSerializer,
)

_INTEGRATION_ENVELOPE_FIELDS = frozenset(
    {
        "event_id",
        "correlation_id",
        "causation_id",
        "occurred_at",
        "aggregate_id",
        "schema_version",
    }
)


class IntegrationEventSerializer(PayloadObjectSerializer):
    """Serializes integration events at the transport boundary."""

    def to_payload(
        self,
        event: object,
        excluded_fields: frozenset[str] | None = None,
    ) -> dict[str, object]:
        if not isinstance(event, IntegrationEvent):
            raise TypeError("IntegrationEventSerializer requires an IntegrationEvent")
        return super().to_payload(
            event,
            excluded_fields=(_INTEGRATION_ENVELOPE_FIELDS | (excluded_fields or frozenset())),
        )

    def to_envelope(
        self,
        event: object,
        *,
        source_service: str,
    ) -> dict[str, object]:
        if not isinstance(event, IntegrationEvent):
            raise TypeError("IntegrationEventSerializer requires an IntegrationEvent")
        return {
            "event_id": event.event_id,
            "source_service": source_service,
            "contract_type": type(event).__name__,
            "occurred_at": event.occurred_at,
            "schema_version": event.schema_version,
            "correlation_id": event.correlation_id,
            "causation_id": event.causation_id,
            "aggregate_id": event.aggregate_id,
            "payload": self.to_payload(event),
        }
