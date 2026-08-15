"""Live RabbitMQ integration tests — outbox → broker → inbox → processor.

Requires the RabbitMQ container from ``shell/rabbitmq/docker-compose.yml``.
Skipped automatically when ``RABBIT_TEST_URL`` is not set.
"""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import aio_pika
from sqlalchemy import select

from shell.definition.infrastructure.definition.persistence.sql.models.base import (
    EVENT_DELIVERY_MODELS,
)
from shell.execution.domain.execution.aggregates.task_execution.events.task_execution_created_event import (
    TaskExecutionCreatedEvent,
)
from shell.execution.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.messaging.event.processor.event_inbox_processor import (
    EventInboxProcessor,
)
from shell.platform.infrastructure.messaging.event.sql_event_outbox_publisher import (
    SqlEventOutboxPublisher,
)
from shell.platform.infrastructure.messaging.transport import OutboxToTransportRelay
from shell.platform.infrastructure.messaging.transport.rabbit import (
    RabbitDeliveryTransport,
    RabbitInboxConsumer,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import async_sessionmaker

import pytest

_INBOX_MODEL: Any = EVENT_DELIVERY_MODELS.inbox

RABBIT_TEST_URL = os.environ.get("RABBIT_TEST_URL", "amqp://shell:shell@localhost:5672")
_rabbit_available = os.environ.get("RABBIT_TEST_URL") is not None

skip_no_rabbit = pytest.mark.skipif(
    not _rabbit_available,
    reason="RABBIT_TEST_URL not set — start shell/rabbitmq/docker-compose.yml to enable",
)


class CollectingBus:
    def __init__(self) -> None:
        self.items: list[object] = []

    async def publish(self, items: Sequence[object]) -> None:
        self.items.extend(items)


def _event() -> TaskExecutionCreatedEvent:
    return TaskExecutionCreatedEvent.now(
        task_execution_id=TaskExecutionId.generate(),
        now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
    )


@skip_no_rabbit
async def test_live_outbox_rabbit_inbox_processor(
    session_factory: async_sessionmaker,
    tmp_path,
) -> None:
    # Purge any leftover messages so the test is deterministic across reruns.
    purge_connection = await aio_pika.connect_robust(RABBIT_TEST_URL)
    purge_channel = await purge_connection.channel()
    purge_queue = await purge_channel.declare_queue("shell-test-event-inbox", durable=True)
    await purge_queue.purge()
    await purge_connection.close()

    # Bind the durable consumer queue first so published messages are routed to it.
    consumer = RabbitInboxConsumer(
        RABBIT_TEST_URL,
        session_factory,
        EVENT_DELIVERY_MODELS,
        queue_name="shell-test-event-inbox",
        routing_keys=["event.#"],
    )
    await consumer.start()

    # Producer writes to the shared outbox DB; consumer inbox lives in the same DB.
    event = _event()
    await SqlEventOutboxPublisher(session_factory, EVENT_DELIVERY_MODELS).publish([event])

    transport = RabbitDeliveryTransport(RABBIT_TEST_URL)
    relay = OutboxToTransportRelay(session_factory, EVENT_DELIVERY_MODELS, transport, kind="event")
    assert await relay.run_once() == 1
    await transport.close()

    # Give the consumer a moment to process the message.
    rows: list[Any] = []
    for _ in range(30):
        await asyncio.sleep(0.2)
        async with session_factory() as session:
            rows = (await session.execute(select(EVENT_DELIVERY_MODELS.inbox))).scalars().all()
        if rows:
            break
    await consumer.close()

    assert len(rows) == 1, "expected one inbox row from the broker"
    assert rows[0].status == InboxStatus.PENDING.value
    assert rows[0].event_type == type(event).__name__

    processor = EventInboxProcessor(
        session_factory,
        CollectingBus(),
        models=EVENT_DELIVERY_MODELS,
        registry={type(event).__name__: type(event)},
    )
    result = await processor.run_once()
    assert result.processed_count == 1

    async with session_factory() as session:
        row = (
            await session.execute(select(_INBOX_MODEL).where(_INBOX_MODEL.id == rows[0].id))
        ).scalar_one()
    assert row.status == InboxStatus.PROCESSED.value
