"""Unit tests for RabbitEventDeliveryTransport delivery semantics.

Verifies the adapter-level contract that protects transactional outbox
at-least-once delivery:
  - every publish uses ``mandatory=True`` so an unroutable message surfaces
    an error instead of being silently dropped by the broker;
  - the underlying channel enables ``on_return_raises`` so Basic.Return is
    turned into an exception that propagates to the relay;
  - any publish failure propagates (the relay must not mark ``published_at``).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

import pytest

from shell.platform.application.ports.transport.event_transport import (
    EventDeliveryEnvelope,
)
from shell.platform.infrastructure.messaging.event_transport.rabbit import (
    rabbit_event_delivery_transport as transport_module,
)
from shell.platform.infrastructure.messaging.event_transport.rabbit.rabbit_event_delivery_transport import (
    RabbitEventDeliveryTransport,
)

if TYPE_CHECKING:
    from aio_pika.abc import AbstractChannel


def _envelope() -> EventDeliveryEnvelope:
    return EventDeliveryEnvelope(
        event_id="event-1",
        contract_type="TaskExecutionCreatedEvent",
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        payload={"task_execution_id": "abc"},
        correlation_id="corr-1",
        causation_id="cause-1",
        source_service="execution",
        destination_service="*",
        aggregate_id="aggregate-1",
    )


class _FakeExchange:
    def __init__(self) -> None:
        self.publish_calls: list[dict[str, object]] = []
        self.error: Exception | None = None

    async def publish(
        self,
        message: object,
        routing_key: str,
        *,
        mandatory: bool,
        **_: object,
    ) -> None:
        self.publish_calls.append(
            {
                "message": message,
                "routing_key": routing_key,
                "mandatory": mandatory,
            }
        )
        if self.error is not None:
            raise self.error


class _FakeChannel:
    def __init__(self, exchange: _FakeExchange) -> None:
        self.is_closed = False
        self._exchange = exchange

    async def get_exchange(self, name: str) -> _FakeExchange:
        return self._exchange

    async def declare_exchange(self, name: str, **_: object) -> _FakeExchange:
        return self._exchange


class _FakeConnection:
    def __init__(self) -> None:
        self.is_closed = False
        self.channel_kwargs: dict[str, object] | None = None

    async def channel(self, **kwargs: object) -> _FakeChannel:
        self.channel_kwargs = kwargs
        return _FakeChannel(_FakeExchange())


class TestRabbitEventDeliveryTransport:
    async def _transport(self, channel: _FakeChannel) -> RabbitEventDeliveryTransport:
        transport = RabbitEventDeliveryTransport(url="amqp://fake")
        transport._channel = cast("AbstractChannel", channel)
        return transport

    async def test_deliver_publishes_with_mandatory_true(self) -> None:
        exchange = _FakeExchange()

        transport = await self._transport(_FakeChannel(exchange))
        await transport.deliver(_envelope())

        assert len(exchange.publish_calls) == 1
        call = exchange.publish_calls[0]
        assert call["mandatory"] is True
        assert call["routing_key"] == "event.TaskExecutionCreatedEvent"

    async def test_unroutable_error_propagates_to_caller(self) -> None:
        exchange = _FakeExchange()
        exchange.error = RuntimeError("NO_ROUTE: unroutable message")

        transport = await self._transport(_FakeChannel(exchange))
        with pytest.raises(RuntimeError, match="NO_ROUTE"):
            await transport.deliver(_envelope())

    async def test_timeout_confirm_error_propagates(self) -> None:
        exchange = _FakeExchange()
        exchange.error = TimeoutError("broker confirmation timed out")

        transport = await self._transport(_FakeChannel(exchange))
        with pytest.raises(TimeoutError):
            await transport.deliver(_envelope())

    async def test_get_channel_enables_return_raises(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        connection = _FakeConnection()

        async def fake_connect_robust(url: str, *, timeout: float) -> _FakeConnection:
            return connection

        monkeypatch.setattr(transport_module, "connect_robust", fake_connect_robust)
        transport = RabbitEventDeliveryTransport(url="amqp://fake")

        channel: Any = await transport._get_channel()

        assert channel is not None
        assert connection.channel_kwargs == {
            "publisher_confirms": True,
            "on_return_raises": True,
        }
