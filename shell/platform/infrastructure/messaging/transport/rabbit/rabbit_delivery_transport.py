"""RabbitDeliveryTransport — DeliveryTransport adapter publishing envelopes to RabbitMQ.

Routing convention:
  exchange  : ``shell.delivery`` (topic exchange)
  routing key: ``{kind}.{delivery_type}``   e.g. ``event.TaskExecutionCreatedEvent``
  message   : JSON envelope bytes (see EnvelopeCodec), persistent delivery mode.

Each consumer BC binds its own queue to the exchange with the routing keys it
handles. Publishing is confirm-based: ``deliver()`` raises on nack/timeout so the
caller (outbox relay) can retry and never lose the record.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from aio_pika import DeliveryMode, Message, connect_robust

from shell.platform.infrastructure.messaging.transport.envelope_codec import EnvelopeCodec

if TYPE_CHECKING:
    from aio_pika.abc import AbstractChannel, AbstractRobustConnection

    from shell.platform.application.ports.transport.delivery_transport import DeliveryEnvelope

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "shell.delivery"


class RabbitDeliveryTransport:
    def __init__(
        self,
        url: str,
        exchange_name: str = EXCHANGE_NAME,
        publisher_confirms: bool = True,
    ) -> None:
        self._url = url
        self._exchange_name = exchange_name
        self._publisher_confirms = publisher_confirms
        self._codec = EnvelopeCodec()
        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractChannel | None = None
        self._lock = asyncio.Lock()

    async def deliver(self, envelope: DeliveryEnvelope) -> None:
        channel = await self._get_channel()
        exchange = await channel.get_exchange(self._exchange_name)
        await exchange.publish(
            Message(
                body=self._codec.encode(envelope),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
            ),
            routing_key=f"{envelope.kind}.{envelope.delivery_type}",
            mandatory=False,
        )

    async def _get_channel(self) -> AbstractChannel:
        async with self._lock:
            if self._channel is not None and not self._channel.is_closed:
                return self._channel
            self._connection = await connect_robust(self._url, timeout=30)
            channel = await self._connection.channel(publisher_confirms=self._publisher_confirms)
            self._channel = channel
            await channel.declare_exchange(
                self._exchange_name,
                type="topic",
                durable=True,
            )
            return channel

    async def close(self) -> None:
        async with self._lock:
            if self._channel is not None and not self._channel.is_closed:
                await self._channel.close()
            if self._connection is not None and not self._connection.is_closed:
                await self._connection.close()
            self._channel = None
            self._connection = None
