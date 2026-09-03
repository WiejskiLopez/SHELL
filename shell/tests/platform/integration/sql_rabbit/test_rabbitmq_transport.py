"""Live RabbitMQ integration tests — outbox → broker → inbox → processor.

Requires the RabbitMQ container from ``shell/rabbitmq/docker/docker-compose.yml``.
Skipped automatically when ``RABBIT_TEST_URL`` is not set.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import aio_pika
import pytest
from aiormq.exceptions import PublishError
from sqlalchemy import select

from shell.execution_service.application.execution.task_execution.integration_events.task_execution_created_integration_event import (
    TaskExecutionCreatedIntegrationEvent,
)
from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.infrastructure.messaging.event.processor.event_inbox_processor import (
    EventInboxProcessor,
)
from shell.platform.infrastructure.messaging.event_transport import EventOutboxToTransportRelay
from shell.platform.infrastructure.messaging.event_transport.rabbit import (
    RabbitEventDeliveryTransport,
    RabbitEventInboxConsumer,
)
from shell.platform.infrastructure.serialization.integration_event.integration_event_serializer import (
    IntegrationEventSerializer,
)
from shell.tests.platform.integration.platform_delivery_models import (
    EVENT_DELIVERY_MODELS,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import async_sessionmaker

_INBOX_MODEL: Any = EVENT_DELIVERY_MODELS.inbox

RABBIT_TEST_URL = os.environ.get("RABBIT_TEST_URL", "amqp://shell:shell@localhost:5672")
_rabbit_available = os.environ.get("RABBIT_TEST_URL") is not None

skip_no_rabbit = pytest.mark.skipif(
    not _rabbit_available,
    reason="RABBIT_TEST_URL not set — start shell/rabbitmq/docker/docker-compose.yml to enable",
)


class CollectingBus:
    def __init__(self) -> None:
        self.items: list[object] = []

    async def publish(self, items: Sequence[object]) -> None:
        self.items.extend(items)


def _event() -> TaskExecutionCreatedIntegrationEvent:
    return TaskExecutionCreatedIntegrationEvent(
        event_id="event-rabbit-1",
        correlation_id="correlation-rabbit-1",
        causation_id="causation-rabbit-1",
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        aggregate_id="task-execution-rabbit-1",
        schema_version=1,
        task_execution_id="task-execution-rabbit-1",
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
    consumer = RabbitEventInboxConsumer(
        RABBIT_TEST_URL,
        session_factory,
        EVENT_DELIVERY_MODELS,
        queue_name="shell-test-event-inbox",
        routing_keys=["event.#"],
    )
    await consumer.start()

    # Producer writes to the shared outbox DB; consumer inbox lives in the same DB.
    event = _event()
    envelope = IntegrationEventSerializer().to_envelope(
        event,
        outbox_id="outbox-rabbit-1",
        source_service="execution_service",
    )
    async with session_factory() as session:
        session.add(
            EVENT_DELIVERY_MODELS.outbox(
                id=envelope["outbox_id"],
                event_id=envelope["event_id"],
                source_service=envelope["source_service"],
                integration_event_name=envelope["integration_event_name"],
                occurred_at=envelope["occurred_at"],
                aggregate_id=envelope["aggregate_id"],
                schema_version=envelope["schema_version"],
                payload=envelope["payload"],
                correlation_id=envelope["correlation_id"],
                causation_id=envelope["causation_id"],
            )
        )
        await session.commit()

    transport = RabbitEventDeliveryTransport(RABBIT_TEST_URL)
    relay = EventOutboxToTransportRelay(session_factory, EVENT_DELIVERY_MODELS, transport)
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
    assert rows[0].integration_event_name == type(event).__name__

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


@skip_no_rabbit
async def test_unroutable_delivery_raises_and_is_retried(
    tmp_path,
) -> None:
    """An unroutable publish (routing key with no binding) must raise
    instead of being silently dropped; after a binding is added the relay
    delivers the same record (at-least-once)."""
    from sqlalchemy.ext.asyncio import create_async_engine

    from shell.platform.infrastructure.persistence.sql import build_session_factory

    outbox_model: Any = EVENT_DELIVERY_MODELS.outbox

    # Isolation: dedicated DB and dedicated exchange, so the shared
    # ``shell.delivery`` exchange bindings of other tests cannot make the
    # routing key routable and the run stays deterministic.
    url = f"sqlite+aiosqlite:///{tmp_path / 'relay-unroutable.db'}"
    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.run_sync(outbox_model.metadata.create_all)
    await engine.dispose()
    isolated = build_session_factory(url)

    # Unikalna nazwa wymiany per run — trwałe leftoverowe bindingi z poprzednich
    # przebiegów (auto-delete nigdy nie odpala, bo kolejka nie miała konsumenta)
    # uczyniłyby routing-key routowalnym i test deterministycznie nie rzucił.
    exchange_name = f"shell.delivery.unroutable-test-{uuid.uuid4().hex[:8]}"

    event = _event()
    envelope = IntegrationEventSerializer().to_envelope(
        event,
        outbox_id="outbox-unroutable-1",
        source_service="execution_service",
    )
    async with isolated() as session:
        session.add(
            outbox_model(
                id=envelope["outbox_id"],
                event_id=envelope["event_id"],
                source_service=envelope["source_service"],
                integration_event_name=envelope["integration_event_name"],
                occurred_at=envelope["occurred_at"],
                aggregate_id=envelope["aggregate_id"],
                schema_version=envelope["schema_version"],
                payload=envelope["payload"],
                correlation_id=envelope["correlation_id"],
                causation_id=envelope["causation_id"],
            )
        )
        await session.commit()

    transport = RabbitEventDeliveryTransport(RABBIT_TEST_URL, exchange_name=exchange_name)
    relay = EventOutboxToTransportRelay(isolated, EVENT_DELIVERY_MODELS, transport)

    # No queue is bound on the dedicated exchange yet → publish must raise.
    with pytest.raises(PublishError):
        await relay.run_once()

    async with isolated() as session:
        rows = (await session.execute(select(outbox_model))).scalars().all()
    assert len(rows) == 1
    assert rows[0].published_at is None

    # Bind a queue for the routing key and retry → the same record is delivered.
    rabbit_connection = await aio_pika.connect_robust(RABBIT_TEST_URL)
    rabbit_channel = await rabbit_connection.channel()
    exchange = await rabbit_channel.declare_exchange(exchange_name, type="topic", durable=True)
    queue = await rabbit_channel.declare_queue(
        "shell-test-unroutable-relay", durable=True, auto_delete=True
    )
    await queue.bind(exchange, routing_key="event.#")
    await queue.purge()

    assert await relay.run_once() == 1

    async with isolated() as session:
        rows = (await session.execute(select(outbox_model))).scalars().all()
    assert rows[0].published_at is not None

    await transport.close()
    await rabbit_channel.close()
    await rabbit_connection.close()
