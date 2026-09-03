"""RabbitCommandInboxConsumer — consumes command envelopes and persists them to the local inbox."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aio_pika import connect_robust
from sqlalchemy.dialects.postgresql import insert as pg_insert

from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.infrastructure.messaging.command_transport.envelope_codec import EnvelopeCodec

if TYPE_CHECKING:
    from aio_pika.abc import (
        AbstractChannel,
        AbstractIncomingMessage,
        AbstractRobustConnection,
    )
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.application.ports.technical_id_generator import TechnicalIdGenerator
    from shell.platform.application.ports.transport.command_transport import (
        CommandDeliveryEnvelope,
    )
    from shell.platform.infrastructure.persistence.sql.models.command_delivery import (
        CommandDeliveryModels,
    )

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "shell.delivery"


class RabbitCommandInboxConsumer:
    """Subscribes to command routing keys and writes durable inbox rows before acking."""

    def __init__(
        self,
        url: str,
        session_factory: async_sessionmaker[AsyncSession],
        models: CommandDeliveryModels,
        service_name: str,
        exchange_name: str = EXCHANGE_NAME,
        id_generator: TechnicalIdGenerator | None = None,
    ) -> None:
        self._url = url
        self._session_factory = session_factory
        self._inbox_model = models.inbox
        self._service_name = service_name
        self._queue_name = f"shell-{service_name}-command-inbox"
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
        await queue.bind(exchange, routing_key=f"command.{self._service_name}.#")
        await queue.consume(self._on_message)

    async def _on_message(self, message: AbstractIncomingMessage) -> None:
        try:
            envelope = self._codec.decode(message.body)
        except (ValueError, KeyError, TypeError):
            logger.exception("Failed to decode command envelope on queue %s; rejecting", self._queue_name)
            await message.reject(requeue=False)
            return

        try:
            await self._persist(envelope)
        except Exception:
            logger.exception("Failed to persist inbox command; requeueing")
            await message.reject(requeue=True)
            return
        await message.ack()

    async def _persist(self, envelope: CommandDeliveryEnvelope) -> None:
        values: dict[str, object] = {
            "id": self._id_generator.new_id(),
            "outbox_id": envelope.outbox_id,
            "command_id": envelope.command_id,
            "command_name": envelope.command_name,
            "source_service": envelope.source_service,
            "target_service": envelope.target_service,
            "schema_version": envelope.schema_version,
            "issued_at": envelope.issued_at,
            "payload": envelope.payload,
            "correlation_id": envelope.correlation_id,
            "causation_id": envelope.causation_id,
            "received_at": envelope.issued_at,
            "status": InboxStatus.PENDING.value,
        }
        async with self._session_factory() as session:
            try:
                await session.execute(
                    pg_insert(self._inbox_model).values(**values).on_conflict_do_nothing()
                )
                await session.commit()
            except Exception:
                logger.exception("Failed to persist inbox command")
                raise

    async def close(self) -> None:
        if self._channel is not None and not self._channel.is_closed:
            await self._channel.close()
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
        self._channel = None
        self._connection = None