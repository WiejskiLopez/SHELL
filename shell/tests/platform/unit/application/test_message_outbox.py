"""Unit tests — message outbox in-memory store and MessageBusPublisher."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from shell.domain.messaging.aggregates.message_router.messages.routable_message import (
    RoutableMessage,
)
from shell.domain.messaging.aggregates.message_router.value_objects.message_data import MessageData
from shell.platform.application.bus.message_bus import MessageBus
from shell.platform.application.bus.message_bus_publisher import MessageBusPublisher
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.context import (
    reset_causation_id,
    reset_correlation_id,
    set_causation_id,
    set_correlation_id,
)
from shell.platform.infrastructure.messaging.memory_outbox_store import InMemoryMessageOutboxStore
from shell.platform.types import JsonStr


def _routable_message() -> RoutableMessage:
    return RoutableMessage(
        occurred_at=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
        message_data=MessageData(JsonStr(json.dumps({"type": "test"}))),
    )


class TestInMemoryMessageOutboxStore:
    async def test_publish_adds_records(self) -> None:
        store = InMemoryMessageOutboxStore()
        await store.publish([_routable_message(), _routable_message()])
        assert len(store.records) == 2

    async def test_pending_returns_unpublished(self) -> None:
        store = InMemoryMessageOutboxStore()
        await store.publish([_routable_message()])
        assert len(store.pending()) == 1

    async def test_records_have_message_type(self) -> None:
        store = InMemoryMessageOutboxStore()
        await store.publish([_routable_message()])
        assert store.records[0].message_type == "RoutableMessage"

    async def test_empty_publish_no_records(self) -> None:
        store = InMemoryMessageOutboxStore()
        await store.publish([])
        assert store.records == []

    async def test_records_have_correlation_id(self) -> None:
        token = set_correlation_id("test-corr-123")
        try:
            store = InMemoryMessageOutboxStore()
            await store.publish([_routable_message()])
            assert store.records[0].correlation_id == "test-corr-123"
        finally:
            reset_correlation_id(token)

    async def test_records_have_causation_id(self) -> None:
        token = set_causation_id("test-caus-456")
        try:
            store = InMemoryMessageOutboxStore()
            await store.publish([_routable_message()])
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
        bus.register(RoutableMessage, _handler_factory)
        publisher = MessageBusPublisher(bus)
        message = _routable_message()
        await publisher.publish([message])
        assert received == [message]
