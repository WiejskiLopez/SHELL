from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from shell.definition_service.application.definition.graph_definition.integration_events.graph_definition_created_integration_event import (
    GraphDefinitionCreatedIntegrationEvent,
)
from shell.definition_service.infrastructure.definition.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
)
from shell.platform.infrastructure.messaging.event.processor.event_inbox_processor import (
    EventInboxProcessor,
)
from shell.platform.infrastructure.messaging.inbox.envelope_validator import (
    EnvelopeValidationPolicy,
)
from shell.platform.infrastructure.messaging.transport import EnvelopeCodec, OutboxToTransportRelay
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.serialization.event.integration_event_serializer import (
    IntegrationEventSerializer,
)
from shell.tests.shared.sql_lifecycle import track_session_factory

if TYPE_CHECKING:
    from collections.abc import Sequence


class RecordingBus:
    def __init__(self) -> None:
        self.events: list[object] = []

    async def publish(self, events: Sequence[object]) -> None:
        self.events.extend(events)


class RecordingTransport:
    def __init__(self) -> None:
        self.envelopes: list[object] = []

    async def deliver(self, envelope: object) -> None:
        self.envelopes.append(envelope)


def _event() -> GraphDefinitionCreatedIntegrationEvent:
    return GraphDefinitionCreatedIntegrationEvent(
        event_id="event-1",
        correlation_id="correlation-1",
        causation_id="causation-1",
        occurred_at=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
        aggregate_id="graph-1",
        aggregate_name="GraphDefinition",
        schema_version=2,
        graph_definition_id="graph-1",
    )


async def test_integration_event_metadata_survives_outbox_transport_inbox_processor(
    tmp_path,
) -> None:
    url = f"sqlite+aiosqlite:///{tmp_path / 'integration-event-contract.db'}"
    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.run_sync(PERSISTENCE_DELIVERY_MODELS.events.outbox.metadata.create_all)
        await connection.run_sync(PERSISTENCE_DELIVERY_MODELS.events.inbox.metadata.create_all)
        await connection.run_sync(
            PERSISTENCE_DELIVERY_MODELS.processed_delivery.metadata.create_all
        )
    await engine.dispose()

    session_factory = build_session_factory(url)
    track_session_factory(session_factory)
    event = _event()
    serializer = IntegrationEventSerializer()
    envelope = serializer.to_envelope(
        event,
        outbox_id="outbox-1",
        source_service="definition_service",
    )

    assert envelope["payload"] == {"graph_definition_id": "graph-1"}
    assert all(
        key not in envelope["payload"]
        for key in (
            "event_id",
            "event_type",
            "occurred_at",
            "schema_version",
            "correlation_id",
            "causation_id",
            "aggregate_id",
            "aggregate_name",
            "source_service",
        )
    )

    async with session_factory() as session:
        session.add(
            PERSISTENCE_DELIVERY_MODELS.events.outbox(
                id=envelope["outbox_id"],
                event_id=envelope["event_id"],
                source_service=envelope["source_service"],
                event_type=envelope["event_type"],
                occurred_at=envelope["occurred_at"],
                aggregate_id=envelope["aggregate_id"],
                aggregate_name=envelope["aggregate_name"],
                schema_version=envelope["schema_version"],
                payload=envelope["payload"],
                correlation_id=envelope["correlation_id"],
                causation_id=envelope["causation_id"],
            )
        )
        await session.commit()

    transport = RecordingTransport()
    relay = OutboxToTransportRelay(
        session_factory,
        PERSISTENCE_DELIVERY_MODELS.events,
        transport,
        kind="event",
    )
    assert await relay.run_once() == 1
    delivered = transport.envelopes[0]

    wire = EnvelopeCodec().encode(delivered)  # type: ignore[arg-type]
    decoded = EnvelopeCodec().decode(wire)
    assert decoded.outbox_id == "outbox-1"
    assert decoded.event_id == "event-1"
    assert decoded.source_service == "definition_service"
    assert decoded.contract_type == "GraphDefinitionCreatedIntegrationEvent"
    assert decoded.schema_version == 2
    assert decoded.occurred_at == event.occurred_at
    assert decoded.correlation_id == event.correlation_id
    assert decoded.causation_id == event.causation_id
    assert decoded.aggregate_id == event.aggregate_id
    assert decoded.aggregate_name == event.aggregate_name
    assert decoded.payload == {"graph_definition_id": "graph-1"}

    async with session_factory() as session:
        session.add(
            PERSISTENCE_DELIVERY_MODELS.events.inbox(
                id="inbox-1",
                outbox_id=decoded.outbox_id,
                event_id=decoded.event_id,
                source_service=decoded.source_service,
                event_type=decoded.contract_type,
                occurred_at=decoded.occurred_at,
                aggregate_id=decoded.aggregate_id,
                aggregate_name=decoded.aggregate_name,
                schema_version=decoded.schema_version,
                payload=decoded.payload,
                correlation_id=decoded.correlation_id,
                causation_id=decoded.causation_id,
                received_at=decoded.occurred_at,
            )
        )
        await session.commit()

    bus = RecordingBus()
    processor = EventInboxProcessor(
        session_factory,
        bus,
        models=PERSISTENCE_DELIVERY_MODELS.events,
        registry={type(event).__name__: type(event)},
        consumer_name="definition-contract-test",
        envelope_policy=EnvelopeValidationPolicy(
            supported_schema_versions={
                type(event).__name__: frozenset({2}),
            }
        ),
    )
    result = await processor.run_once()

    assert result.processed_count == 1
    assert len(bus.events) == 1
    restored = bus.events[0]
    assert isinstance(restored, GraphDefinitionCreatedIntegrationEvent)
    assert restored.event_id == event.event_id
    assert restored.schema_version == event.schema_version
    assert restored.graph_definition_id == event.graph_definition_id

    async with session_factory() as session:
        inbox_model: Any = PERSISTENCE_DELIVERY_MODELS.events.inbox
        inbox_row = (
            await session.execute(select(inbox_model).where(inbox_model.id == "inbox-1"))
        ).scalar_one()
    inbox: Any = inbox_row
    assert inbox.outbox_id == "outbox-1"
    assert inbox.source_service == "definition_service"
