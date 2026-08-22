from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

from shell.platform.application.events.integration_event import IntegrationEvent
from shell.platform.domain.events import DomainEvent
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.serialization.event.domain_event_serializer import (
    DomainEventSerializer,
)
from shell.platform.infrastructure.serialization.event.event_deserializer import EventDeserializer
from shell.platform.infrastructure.serialization.event.event_envelope_serializer import (
    EventEnvelopeSerializer,
)
from shell.platform.infrastructure.serialization.event.integration_event_serializer import (
    IntegrationEventSerializer,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class SampleEvent(DomainEvent):
    name: str
    created_at: CreatedAt


@dataclass(frozen=True, slots=True)
class SampleIntegrationEvent(IntegrationEvent):
    name: str


def _sample_event() -> SampleEvent:
    timestamp = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
    return SampleEvent(
        occurred_at=OccurredAt.from_datetime(timestamp),
        name="created",
        created_at=CreatedAt.from_datetime(timestamp),
    )


def _sample_integration_event() -> SampleIntegrationEvent:
    return SampleIntegrationEvent(
        event_id="event-1",
        correlation_id="correlation-1",
        causation_id="causation-1",
        occurred_at=datetime(2026, 8, 20, 12, 0, tzinfo=UTC),
        aggregate_id="aggregate-1",
        aggregate_name="Sample",
        schema_version=3,
        name="created",
    )


def test_event_serializer_excludes_envelope_metadata_from_payload() -> None:
    event = _sample_event()

    payload = DomainEventSerializer().to_payload(event)

    assert payload["name"] == "created"
    assert payload["created_at"] == "2026-08-20T12:00:00+00:00"
    assert "occurred_at" not in payload
    assert "schema_version" not in payload


def test_integration_event_serializer_excludes_all_envelope_metadata() -> None:
    payload = IntegrationEventSerializer().to_payload(_sample_integration_event())

    assert payload == {"name": "created"}


def test_integration_event_serializer_builds_envelope_separately() -> None:
    envelope = IntegrationEventSerializer().to_envelope(
        _sample_integration_event(), outbox_id="outbox-1", source_service="sample_service"
    )

    assert envelope["event_type"] == "SampleIntegrationEvent"
    assert envelope["event_id"] == "event-1"
    assert envelope["schema_version"] == 3
    assert envelope["payload"] == {"name": "created"}


def test_event_round_trip_preserves_domain_value_object_types() -> None:
    event = _sample_event()
    serializer = DomainEventSerializer()
    envelope = EventEnvelopeSerializer(serializer).to_outbox_payload(event)

    restored = EventDeserializer(registry={"SampleEvent": SampleEvent}).deserialize(
        event_type=cast("str", envelope["event_type"]),
        occurred_at=cast("datetime", envelope["occurred_at"]),
        payload=cast("dict[str, object]", envelope["payload"]),
    )

    assert isinstance(restored, SampleEvent)
    assert isinstance(restored.occurred_at, OccurredAt)
    assert isinstance(restored.created_at, CreatedAt)
    assert restored.occurred_at == event.occurred_at
    assert restored.created_at == event.created_at


def test_integration_event_round_trip_preserves_datetime_and_integer_schema_version() -> None:
    event = _sample_integration_event()
    envelope = IntegrationEventSerializer().to_envelope(
        event, outbox_id="outbox-1", source_service="sample_service"
    )

    restored = EventDeserializer(
        registry={"SampleIntegrationEvent": SampleIntegrationEvent}
    ).deserialize(
        event_type="SampleIntegrationEvent",
        occurred_at=cast("datetime", envelope["occurred_at"]),
        payload=cast("dict[str, object]", envelope["payload"]),
        schema_version=event.schema_version,
        event_id=cast("str", envelope["event_id"]),
        correlation_id=cast("str", envelope["correlation_id"]),
        causation_id=cast("str", envelope["causation_id"]),
        aggregate_id=cast("str", envelope["aggregate_id"]),
        aggregate_name=cast("str", envelope["aggregate_name"]),
    )

    assert isinstance(restored, SampleIntegrationEvent)
    assert isinstance(restored.occurred_at, datetime)
    assert restored.occurred_at == event.occurred_at
    assert restored.schema_version == event.schema_version
    assert envelope["source_service"] == "sample_service"


def test_event_deserializer_returns_none_for_invalid_typed_payload() -> None:
    event = _sample_event()
    payload = DomainEventSerializer().to_payload(event)

    restored = EventDeserializer(registry={"SampleEvent": SampleEvent}).deserialize(
        event_type="SampleEvent",
        occurred_at=cast("datetime", "not-a-datetime"),
        payload=payload,
    )

    assert restored is None


def test_domain_event_envelope_serializer_rejects_integration_event() -> None:
    try:
        EventEnvelopeSerializer().to_outbox_payload(_sample_integration_event())
    except TypeError as exc:
        assert "DomainEvent" in str(exc)
    else:
        raise AssertionError("expected DomainEvent-only envelope serializer")
