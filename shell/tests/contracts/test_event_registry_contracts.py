"""Contract tests for bounded-context event registries."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

from shell.definition.application.definition.graph_definition.integration_events.graph_definition_created_integration_event import (
    GraphDefinitionCreatedIntegrationEvent,
)
from shell.definition.bootstrap.definition.event_registry import (
    build_definition_event_registry,
)
from shell.platform.infrastructure.serialization.event_deserializer import EventDeserializer
from shell.platform.infrastructure.serialization.event_serializer import DomainEventSerializer


def test_definition_event_round_trips_through_its_registry() -> None:
    event = GraphDefinitionCreatedIntegrationEvent(
        event_id="event-1",
        correlation_id="correlation-1",
        causation_id="causation-1",
        occurred_at=datetime(2026, 8, 12, tzinfo=UTC),
        aggregate_id="graph-1",
        aggregate_name="GraphDefinition",
        schema_version=1,
        graph_definition_id="graph-1",
    )
    serializer = DomainEventSerializer()
    outbox_payload = serializer.to_outbox_payload(event)

    restored = EventDeserializer(build_definition_event_registry()).deserialize(
        cast("str", outbox_payload["event_type"]),
        event.occurred_at,
        cast("dict[str, object]", outbox_payload["payload"]),
    )

    assert isinstance(restored, GraphDefinitionCreatedIntegrationEvent)
    assert restored.graph_definition_id == event.graph_definition_id
    assert restored.aggregate_id == event.aggregate_id


def test_registry_returns_none_for_unknown_event_type() -> None:
    deserializer = EventDeserializer(build_definition_event_registry())

    restored = deserializer.deserialize(
        "EventFromUnknownBoundedContext",
        datetime(2026, 8, 12, tzinfo=UTC),
        {},
    )

    assert restored is None
