"""RabbitCommandDeliveryTransport — publishes command envelopes to RabbitMQ.

   exchange  : ``shell.delivery`` (topic)
            routing key: ``command.<target_service>.<command_name>``
   message   : JSON envelope bytes (see the command EnvelopeCodec), persistent delivery mode.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from aio_pika import DeliveryMode, Message, connect_robust

from shell.platform.infrastructure.messaging.command_transport.envelope_codec import EnvelopeCodec

if TYPE_CHECKING:
    from aio_pika.abc import AbstractChannel, AbstractRobustConnection

    from shell.platform.application.ports.transport.command_transport import (
        CommandDeliveryEnvelope,
    )

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "shell.delivery"


class RabbitCommandDeliveryTransport:
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

    async def deliver(self, envelope: CommandDeliveryEnvelope) -> None:
        channel = await self._get_channel()
        exchange = await channel.get_exchange(self._exchange_name)
        routing_key = f"command.{envelope.target_service}.{envelope.command_name}"
        try:
            await exchange.publish(
                Message(
                    body=self._codec.encode(envelope),
                    delivery_mode=DeliveryMode.PERSISTENT,
                    content_type="application/json",
                ),
                routing_key=routing_key,
                mandatory=True,
            )
        except Exception:
            logger.exception(
                "RabbitMQ command delivery failed — exchange=%s routing_key=%s outbox_id=%s",
                self._exchange_name,
                routing_key,
                envelope.outbox_id,
            )
            raise

    async def _get_channel(self) -> AbstractChannel:
        async with self._lock:
            if self._channel is not None and not self._channel.is_closed:
                return self._channel
            self._connection = await connect_robust(self._url, timeout=30)
            channel = await self._connection.channel(
                publisher_confirms=self._publisher_confirms,
                on_return_raises=self._publisher_confirms,
            )
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