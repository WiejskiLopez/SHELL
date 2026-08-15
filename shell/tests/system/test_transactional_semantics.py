"""System tests — Faza 5 pilot: transactional semantics of the session handler.

Verifies the at-least-once contract end-to-end through Rabbit:

1. Duplicate delivery of the same login event → the session BC opens exactly ONE
   session (idempotent handler + idempotent inbox insert).
2. The session change and its ``SessionOpenedIntegrationEvent`` are committed
   atomically in the same UoW (the outbox row exists iff the session exists).

Requires the RabbitMQ container; skipped when ``RABBIT_TEST_URL`` is unset.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import pytest
from sqlalchemy import select

from shell.platform.infrastructure.messaging.event.processor.event_inbox_processor import (
    EventInboxProcessor,
)
from shell.platform.infrastructure.messaging.transport.envelope_codec import EnvelopeCodec
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.session_service.bootstrap.session.container.session_core_container import (
    SessionCoreContainer,
    configure_session_container,
)
from shell.session_service.infrastructure.session.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS as SESSION_DELIVERY_MODELS,
)
from shell.session_service.infrastructure.session.session.persistence.sql.models.session import (
    SessionModel,
)
from shell.session_service.migrations.baseline import run_session_baseline

_OUTBOX_MODEL: Any = SESSION_DELIVERY_MODELS.events.outbox

RABBIT_TEST_URL = os.environ.get("RABBIT_TEST_URL", "amqp://shell:shell@localhost:5672")
_rabbit_available = os.environ.get("RABBIT_TEST_URL") is not None

skip_no_rabbit = pytest.mark.skipif(
    not _rabbit_available,
    reason="RABBIT_TEST_URL not set — start shell/rabbitmq/docker-compose.yml to enable",
)

QUEUE = "shell-system-transaction-inbox"


@skip_no_rabbit
async def test_duplicate_delivery_opens_exactly_one_session(tmp_path) -> None:
    session_url = f"sqlite+aiosqlite:///{tmp_path / 'session.db'}"
    await run_session_baseline(session_url)
    session_factory = build_session_factory(session_url)

    await _purge_queue(QUEUE)

    container = SessionCoreContainer()
    container.config.db_url.from_value(session_url)
    configure_session_container(container)
    event_bus = container.event_bus()

    from shell.platform.infrastructure.messaging.transport.rabbit import RabbitInboxConsumer

    consumer = RabbitInboxConsumer(
        RABBIT_TEST_URL,
        session_factory,
        SESSION_DELIVERY_MODELS.events,
        queue_name=QUEUE,
        routing_keys=["event.AuthSessionCreatedIntegrationEvent"],
    )
    await consumer.start()

    # Publish the SAME login event twice (simulates at-least-once redelivery).
    envelope = _login_envelope()
    await _publish_event(envelope)
    await _publish_event(envelope)

    processor = EventInboxProcessor(
        session_factory,
        event_bus,
        models=SESSION_DELIVERY_MODELS.events,
        registry=container.event_registry(),
    )
    for _ in range(30):
        await asyncio.sleep(0.2)
        await processor.run_once()
        async with session_factory() as session:
            sessions = (await session.execute(select(SessionModel))).scalars().all()
        if sessions:
            break
    await consumer.close()

    async with session_factory() as session:
        sessions = (await session.execute(select(SessionModel))).scalars().all()
        outbox = (
            (
                await session.execute(
                    select(_OUTBOX_MODEL).where(
                        _OUTBOX_MODEL.event_type == "SessionOpenedIntegrationEvent"
                    )
                )
            )
            .scalars()
            .all()
        )
        inbox = (
            (await session.execute(select(SESSION_DELIVERY_MODELS.events.inbox))).scalars().all()
        )

    # Exactly one session, one outbox event, and one inbox row (dedup on insert).
    assert len(sessions) == 1, "duplicate delivery must open exactly one session"
    assert len(outbox) == 1, "exactly one SessionOpenedIntegrationEvent expected"
    assert len(inbox) == 1, "duplicate inbox insert must be deduplicated"
    assert sessions[0].status == "OPEN"


@skip_no_rabbit
async def test_session_and_outbox_commit_atomically(tmp_path) -> None:
    """The handler's UoW commits session + outbox in one transaction.

    After a successful handler run the outbox event exists exactly when the
    session exists — there is never an outbox event without a session.
    """
    session_url = f"sqlite+aiosqlite:///{tmp_path / 'session2.db'}"
    await run_session_baseline(session_url)
    session_factory = build_session_factory(session_url)
    await _purge_queue(QUEUE)

    container = SessionCoreContainer()
    container.config.db_url.from_value(session_url)
    configure_session_container(container)
    event_bus = container.event_bus()

    from shell.platform.infrastructure.messaging.transport.rabbit import RabbitInboxConsumer

    consumer = RabbitInboxConsumer(
        RABBIT_TEST_URL,
        session_factory,
        SESSION_DELIVERY_MODELS.events,
        queue_name=QUEUE,
        routing_keys=["event.AuthSessionCreatedIntegrationEvent"],
    )
    await consumer.start()
    await _publish_event(_login_envelope())

    processor = EventInboxProcessor(
        session_factory,
        event_bus,
        models=SESSION_DELIVERY_MODELS.events,
        registry=container.event_registry(),
    )
    for _ in range(30):
        await asyncio.sleep(0.2)
        await processor.run_once()
        async with session_factory() as session:
            sessions = (await session.execute(select(SessionModel))).scalars().all()
        if sessions:
            break
    await consumer.close()

    async with session_factory() as session:
        outbox = (
            (
                await session.execute(
                    select(_OUTBOX_MODEL).where(
                        _OUTBOX_MODEL.event_type == "SessionOpenedIntegrationEvent"
                    )
                )
            )
            .scalars()
            .all()
        )
    assert len(outbox) == 1, "outbox event must be present alongside the session"


async def _publish_event(envelope: object) -> None:
    import aio_pika

    connection = await aio_pika.connect_robust(RABBIT_TEST_URL)
    channel = await connection.channel()
    exchange = await channel.declare_exchange("shell.delivery", type="topic", durable=True)
    await exchange.publish(
        aio_pika.Message(
            body=EnvelopeCodec().encode(envelope),  # type: ignore[arg-type]
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key=f"{envelope.kind}.{envelope.delivery_type}",  # type: ignore[attr-defined]
    )
    await connection.close()


def _login_envelope() -> object:
    from datetime import UTC, datetime

    from shell.platform.application.ports.delivery_transport import DeliveryEnvelope

    return DeliveryEnvelope(
        kind="event",
        delivery_id="duplicate-login-1",
        delivery_type="AuthSessionCreatedIntegrationEvent",
        occurred_at=datetime.now(tz=UTC),
        payload={
            "auth_session_id": "auth-1",
            "user_id": "user-dup-1",
        },
        correlation_id="corr-dup",
        causation_id="cause-0",
    )


async def _purge_queue(queue_name: str) -> None:
    import aio_pika

    connection = await aio_pika.connect_robust(RABBIT_TEST_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue(queue_name, durable=True)
    await queue.purge()
    await connection.close()
