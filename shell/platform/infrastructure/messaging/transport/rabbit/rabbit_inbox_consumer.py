"""RabbitInboxConsumer — consumes delivery envelopes and persists them to the local inbox.

Consumer-side bridge between the broker and the bounded-context inbox:
  - subscribes to a queue bound to the ``shell.delivery`` topic exchange;
  - decodes each message into a DeliveryEnvelope;
  - idempotently inserts into the local ``inbox_*`` table (ON CONFLICT DO NOTHING);
  - acks the broker message ONLY after the inbox write is durable.

A crash after insert but before ack re-delivers the message; the idempotent insert
makes that harmless (at-least-once). A poisoned message that fails to decode is
rejected (nack, no requeue) so it does not block the queue.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aio_pika import connect_robust
from sqlalchemy.dialects.postgresql import insert as pg_insert

from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.infrastructure.messaging.transport.envelope_codec import EnvelopeCodec

if TYPE_CHECKING:
    from aio_pika.abc import (
        AbstractChannel,
        AbstractIncomingMessage,
        AbstractRobustConnection,
    )
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.application.ports.delivery_transport import DeliveryEnvelope
    from shell.platform.infrastructure.persistence.sql.models.command_delivery import (
        CommandDeliveryModels,
    )
    from shell.platform.infrastructure.persistence.sql.models.event_delivery import (
        EventDeliveryModels,
    )
    from shell.platform.infrastructure.persistence.sql.models.message_delivery import (
        MessageDeliveryModels,
    )

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "shell.delivery"


class RabbitInboxConsumer:
    def __init__(
        self,
        url: str,
        session_factory: async_sessionmaker[AsyncSession],
        models: EventDeliveryModels | MessageDeliveryModels | CommandDeliveryModels,
        queue_name: str,
        routing_keys: list[str] | None = None,
        exchange_name: str = EXCHANGE_NAME,
    ) -> None:
        self._url = url
        self._session_factory = session_factory
        self._inbox_model = models.inbox
        self._queue_name = queue_name
        self._routing_keys = routing_keys or ["#"]
        self._exchange_name = exchange_name
        self._codec = EnvelopeCodec()
        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractChannel | None = None

    async def start(self) -> None:
        self._connection = await connect_robust(self._url, timeout=30)
        channel = await self._connection.channel()
        self._channel = channel
        await channel.set_qos(prefetch_count=10)
        exchange = await channel.declare_exchange(self._exchange_name, type="topic", durable=True)
        queue = await channel.declare_queue(self._queue_name, durable=True)
        for routing_key in self._routing_keys:
            await queue.bind(exchange, routing_key=routing_key)
        await queue.consume(self._on_message)

    async def _on_message(self, message: AbstractIncomingMessage) -> None:
        try:
            envelope = self._codec.decode(message.body)
        except (ValueError, KeyError, TypeError):
            logger.exception("Failed to decode envelope on queue %s; rejecting", self._queue_name)
            await message.reject(requeue=False)
            return

        persisted = await self._persist(envelope)
        if persisted:
            await message.ack()
        else:
            await message.reject(requeue=False)

    async def _persist(self, envelope: DeliveryEnvelope) -> bool:
        type_column = f"{envelope.kind}_type"
        values = {
            "id": envelope.delivery_id,
            type_column: envelope.delivery_type,
            "occurred_at": envelope.occurred_at,
            "payload": envelope.payload,
            "correlation_id": envelope.correlation_id,
            "causation_id": envelope.causation_id,
            "received_at": envelope.occurred_at,
            "status": InboxStatus.PENDING.value,
        }
        async with self._session_factory() as session:
            try:
                await session.execute(
                    pg_insert(self._inbox_model).values(**values).on_conflict_do_nothing()
                )
                await session.commit()
            except Exception:
                logger.exception("Failed to persist inbox delivery")
                return False
        return True

    async def close(self) -> None:
        if self._channel is not None and not self._channel.is_closed:
            await self._channel.close()
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
        self._channel = None
        self._connection = None
