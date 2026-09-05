from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

from shell.platform.application.events.integration_event import IntegrationEvent
from shell.platform.infrastructure.serialization.integration_event.integration_event_deserializer import (
    IntegrationEventDeserializer,
)
from shell.platform.infrastructure.serialization.integration_event.integration_event_serializer import (
    IntegrationEventSerializer,
)


@dataclass(frozen=True, slots=True)
class SampleIntegrationEvent(IntegrationEvent):
    name: str


def _sample_integration_event() -> SampleIntegrationEvent:
    return SampleIntegrationEvent(
        event_id="event-1",
        correlation_id="correlation-1",
        causation_id="causation-1",
        occurred_at=datetime(2026, 8, 20, 12, 0, tzinfo=UTC),
        aggregate_id="aggregate-1",
        schema_version=3,
        name="created",
    )


def test_integration_event_serializer_excludes_all_envelope_metadata() -> None:
    payload = IntegrationEventSerializer().to_payload(_sample_integration_event())

    assert payload == {"name": "created"}


def test_integration_event_serializer_builds_envelope_separately() -> None:
    envelope = IntegrationEventSerializer().to_envelope(
        _sample_integration_event(), source_service="sample_service"
    )

    assert envelope["contract_type"] == "SampleIntegrationEvent"
    assert envelope["event_id"] == "event-1"
    assert envelope["schema_version"] == 3
    assert envelope["payload"] == {"name": "created"}


def test_integration_event_round_trip_preserves_datetime_and_integer_schema_version() -> None:
    event = _sample_integration_event()
    envelope = IntegrationEventSerializer().to_envelope(
        event, source_service="sample_service"
    )

    restored = IntegrationEventDeserializer(
        registry={"SampleIntegrationEvent": SampleIntegrationEvent}
    ).deserialize(
        integration_event_name="SampleIntegrationEvent",
        occurred_at=cast("datetime", envelope["occurred_at"]),
        payload=cast("dict[str, object]", envelope["payload"]),
        schema_version=event.schema_version,
        event_id=cast("str", envelope["event_id"]),
        correlation_id=cast("str", envelope["correlation_id"]),
        causation_id=cast("str", envelope["causation_id"]),
        aggregate_id=cast("str", envelope["aggregate_id"]),
    )

    assert isinstance(restored, SampleIntegrationEvent)
    assert isinstance(restored.occurred_at, datetime)
    assert restored.occurred_at == event.occurred_at
    assert restored.schema_version == event.schema_version
    assert envelope["source_service"] == "sample_service"