"""Unit tests — message outbox in-memory store and MessageBusPublisher."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from shell.ingestion_service.domain.ingestion.aggregates.ingestion.payloads.ingestion_payload import (
    IngestionPayload,
)
from shell.ingestion_service.domain.ingestion.aggregates.ingestion.value_objects.ingestion_data import (
    IngestionData,
)
from shell.platform.application.bus.message_bus import MessageBus
from shell.platform.application.bus.message_bus_publisher import MessageBusPublisher
from shell.platform.domain.value_objects.aggregate_id import AggregateId
from shell.platform.domain.value_objects.aggregate_name import AggregateName
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.infrastructure.context import (
    reset_causation_id,
    reset_correlation_id,
    set_causation_id,
    set_correlation_id,
)
from shell.platform.infrastructure.messaging.memory_outbox_store import InMemoryMessageOutboxStore
from shell.platform.types import JsonStr


def _ingestion_payload() -> IngestionPayload:
    return IngestionPayload(
        occurred_at=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
        ingestion_data=IngestionData(JsonStr(json.dumps({"type": "test"}))),
        recipient_aggregate_id=AggregateId("agent-1"),
        recipient_aggregate_name=AggregateName("Agent"),
        state_data=StateData(JsonStr.from_object({"type": "test"})),
    )


class TestInMemoryMessageOutboxStore:
    async def test_publish_adds_records(self) -> None:
        store = InMemoryMessageOutboxStore()
        await store.publish([_ingestion_payload(), _ingestion_payload()])
        assert len(store.records) == 2

    async def test_pending_returns_unpublished(self) -> None:
        store = InMemoryMessageOutboxStore()
        await store.publish([_ingestion_payload()])
        assert len(store.pending()) == 1

    async def test_records_have_message_type(self) -> None:
        store = InMemoryMessageOutboxStore()
        await store.publish([_ingestion_payload()])
        assert store.records[0].message_type == "IngestionPayload"

    async def test_empty_publish_no_records(self) -> None:
        store = InMemoryMessageOutboxStore()
        await store.publish([])
        assert store.records == []

    async def test_records_have_correlation_id(self) -> None:
        token = set_correlation_id("test-corr-123")
        try:
            store = InMemoryMessageOutboxStore()
            await store.publish([_ingestion_payload()])
            assert store.records[0].correlation_id == "test-corr-123"
        finally:
            reset_correlation_id(token)

    async def test_records_have_causation_id(self) -> None:
        token = set_causation_id("test-caus-456")
        try:
            store = InMemoryMessageOutboxStore()
            await store.publish([_ingestion_payload()])
            assert store.records[0].causation_id == "test-caus-456"
        finally:
            reset_causation_id(token)


class TestMessageBusPublisher:
    async def test_publish_dispatches_to_bus(self) -> None:
        received: list[object] = []

        class _Handler:
            async def handle(self, message: object) -> None:
                received.append(message)

        def _handler_factory() -> _Handler:
            return _Handler()

        bus = MessageBus()
        bus.register(IngestionPayload, _handler_factory)
        publisher = MessageBusPublisher(bus)
        message = _ingestion_payload()
        await publisher.publish([message])
        assert received == [message]
