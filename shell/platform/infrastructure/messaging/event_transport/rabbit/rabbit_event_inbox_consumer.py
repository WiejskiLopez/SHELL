"""RabbitEventInboxConsumer — consumes integration-event envelopes and persists them to the local inbox."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aio_pika import connect_robust
from sqlalchemy.dialects.postgresql import insert as pg_insert

from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.infrastructure.messaging.event_transport.envelope_codec import EnvelopeCodec

if TYPE_CHECKING:
    from aio_pika.abc import (
        AbstractChannel,
        AbstractIncomingMessage,
        AbstractRobustConnection,
    )
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.application.ports.technical_id_generator import TechnicalIdGenerator
    from shell.platform.application.ports.transport.event_transport import (
        IntegrationEventDeliveryEnvelope,
    )
    from shell.platform.infrastructure.persistence.sql.models.event_delivery import (
        EventDeliveryModels,
    )

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "shell.delivery"


class RabbitEventInboxConsumer:
    """Subscribes to event routing keys and writes durable inbox rows before acking."""

    def __init__(
        self,
        url: str,
        session_factory: async_sessionmaker[AsyncSession],
        models: EventDeliveryModels,
        queue_name: str,
        routing_keys: list[str] | None = None,
        exchange_name: str = EXCHANGE_NAME,
        id_generator: TechnicalIdGenerator | None = None,
    ) -> None:
        self._url = url
        self._session_factory = session_factory
        self._inbox_model = models.inbox
        self._queue_name = queue_name
        self._routing_keys = routing_keys or ["event.#"]
        self._exchange_name = exchange_name
        self._codec = EnvelopeCodec()
        from shell.platform.infrastructure.identity.uuid_technical_id_generator import (
            UuidTechnicalIdGenerator,
        )

        self._id_generator = id_generator or UuidTechnicalIdGenerator()
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
            logger.exception("Failed to decode event envelope on queue %s; rejecting", self._queue_name)
            await message.reject(requeue=False)
            return

        try:
            persisted = await self._persist(envelope)
        except Exception:
            logger.exception("Failed to persist inbox event; requeueing")
            await message.reject(requeue=True)
            return
        if persisted:
            await message.ack()
        else:
            await message.ack()

    async def _persist(self, envelope: IntegrationEventDeliveryEnvelope) -> bool:
        values: dict[str, object] = {
            "id": self._id_generator.new_id(),
            "outbox_id": envelope.outbox_id,
            "event_id": envelope.event_id,
            "source_service": envelope.source_service,
            "integration_event_name": envelope.integration_event_name,
            "occurred_at": envelope.occurred_at,
            "aggregate_id": envelope.aggregate_id,
            "schema_version": envelope.schema_version,
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
                logger.exception("Failed to persist inbox event")
                raise
        return True

    async def close(self) -> None:
        if self._channel is not None and not self._channel.is_closed:
            await self._channel.close()
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
        self._channel = None
        self._connection = None