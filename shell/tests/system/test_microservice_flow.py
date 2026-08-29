"""System tests — full microservice flow User → Rabbit → Session.

Exercise the complete pipeline the way it works between two real bounded contexts:

  User BC (login) → outbox_event (user) → OutboxToTransportRelay → RabbitMQ
      → RabbitInboxConsumer (session) → inbox_event (session) → EventInboxProcessor
      → AuthSessionCreatedEventHandler → opens a Session → outbox_event (session).

Requires the RabbitMQ container from ``shell/rabbitmq/docker/docker-compose.yml``; skipped
automatically when ``RABBIT_TEST_URL`` is not set.
"""

from __future__ import annotations

import asyncio
import os
from datetime import timedelta
from typing import Any

import pytest
from sqlalchemy import select

from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.time.system_clock import SystemClock
from shell.session_service.bootstrap.session.container.session_core_container import (
    SessionCoreContainer,
    configure_session_container,
)
from shell.session_service.infrastructure.session.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS as SESSION_DELIVERY_MODELS,
)
from shell.session_service.migrations.baseline import run_session_baseline
from shell.tests.shared.sql_lifecycle import track_session_factory
from shell.user_service.application.user.auth_session.command_handlers.login_auth_session_handler import (
    LoginAuthSessionHandler,
)
from shell.user_service.application.user.auth_session.commands.login_auth_session_command import (
    LoginAuthSessionCommand,
)
from shell.user_service.bootstrap.user.container.user_core_container import (
    UserCoreContainer,
    configure_user_container,
)
from shell.user_service.infrastructure.user.auth_session.adapters.token_generator.secure_token_generator import (
    SecureTokenGenerator,
)
from shell.user_service.infrastructure.user.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS as USER_DELIVERY_MODELS,
)
from shell.user_service.migrations.baseline import run_user_baseline

_USER_OUTBOX_MODEL: Any = USER_DELIVERY_MODELS.events.outbox
_SESSION_INBOX_MODEL: Any = SESSION_DELIVERY_MODELS.events.inbox
_SESSION_OUTBOX_MODEL: Any = SESSION_DELIVERY_MODELS.events.outbox

RABBIT_TEST_URL = os.environ.get("RABBIT_TEST_URL", "amqp://shell:shell@localhost:5672")
_rabbit_available = os.environ.get("RABBIT_TEST_URL") is not None

skip_no_rabbit = pytest.mark.skipif(
    not _rabbit_available,
    reason="RABBIT_TEST_URL not set — start shell/rabbitmq/docker/docker-compose.yml to enable",
)

USER_QUEUE = "shell-session-event-inbox"


@skip_no_rabbit
async def test_user_login_opens_session_in_session_bc(tmp_path) -> None:
    # ── 1. Two independent BC databases ─────────────────────────────
    user_url = f"sqlite+aiosqlite:///{tmp_path / 'user.db'}"
    session_url = f"sqlite+aiosqlite:///{tmp_path / 'session.db'}"
    await run_user_baseline(user_url)
    await run_session_baseline(session_url)
    user_factory = build_session_factory(user_url)
    session_factory = build_session_factory(session_url)
    track_session_factory(user_factory)
    track_session_factory(session_factory)

    # ── 2. Purge queue for deterministic reruns ─────────────────────
    await _purge_queue(USER_QUEUE)

    # ── 3. Session BC consumer is up first (durable queue binding) ──
    session_container = SessionCoreContainer()
    session_container.config.db_url.from_value(session_url)
    session_container.config.broker_url.from_value(RABBIT_TEST_URL)
    configure_session_container(session_container)
    track_session_factory(session_container.session_factory())

    consumer = session_container.rabbit_inbox_consumer_factory()
    await consumer.start()

    # ── 4. User logs in → AuthSessionCreated → outbox (user) ────────
    user_container = UserCoreContainer()
    user_container.config.db_url.from_value(user_url)
    user_container.config.broker_url.from_value(RABBIT_TEST_URL)
    configure_user_container(user_container)
    track_session_factory(user_container.session_factory())
    unit_of_work = user_container.unit_of_work_factory()
    login_handler = LoginAuthSessionHandler(
        unit_of_work=unit_of_work,
        user_query_provider=user_container.user_query_provider(),
        clock=SystemClock(),
        token_generator=SecureTokenGenerator(),
        id_generator=UuidIdGenerator(),
        session_ttl=timedelta(hours=24),
    )

    # Pre-create a user so login succeeds.
    from shell.user_service.application.user.user.command_handlers.create_user_handler import (
        CreateUserHandler,
    )
    from shell.user_service.application.user.user.commands.create_user_command import (
        CreateUserCommand,
    )

    await CreateUserHandler(
        user_container.unit_of_work_factory(),
        clock=SystemClock(),
        id_generator=UuidIdGenerator(),
    ).handle(CreateUserCommand(email="flow@example.com"))

    login_result = await login_handler.handle(LoginAuthSessionCommand(email="flow@example.com"))
    assert login_result.token

    # ── 5. Transport: outbox (user) → Rabbit (via container provider) ─
    relay = user_container.outbox_to_transport_relay_factory()
    delivered = await relay.run_once()
    assert delivered >= 1  # at least the AuthSessionCreatedIntegrationEvent

    # Only integration events ever reach the outbox (domain events are mapped).
    async with user_factory() as session:
        outbox_types = {
            row.event_type for row in (await session.execute(select(_USER_OUTBOX_MODEL))).scalars()
        }
    assert outbox_types, "expected outbox rows"
    assert all("IntegrationEvent" in event_type for event_type in outbox_types), (
        f"outbox must contain only integration events, got: {sorted(outbox_types)}"
    )

    # ── 6. Wait for consumer → session inbox → processor → handler ──
    processor = session_container.event_inbox_processor_factory()
    for _ in range(30):
        await asyncio.sleep(0.2)
        await processor.run_once()
        async with session_factory() as session:
            sessions = (await session.execute(select(_SESSION_INBOX_MODEL))).scalars().all()
        if sessions:
            break
    await consumer.close()

    # ── 7. Assert the session BC opened a session for the user ──────
    async with session_factory() as session:
        rows = (await session.execute(select(_SESSION_INBOX_MODEL))).scalars().all()
    assert rows, "expected the AuthSessionCreated event in the session inbox"
    assert rows[0].event_type == "AuthSessionCreatedIntegrationEvent"

    async with session_factory() as session:
        opened = (
            (
                await session.execute(
                    select(_SESSION_OUTBOX_MODEL).where(
                        _SESSION_OUTBOX_MODEL.event_type == "SessionOpenedIntegrationEvent"
                    )
                )
            )
            .scalars()
            .all()
        )
    assert opened, "expected SessionOpenedIntegrationEvent in the session outbox"

    # The handler opened exactly one OPEN session for the user.
    from shell.session_service.infrastructure.session.session.persistence.sql.models.session import (
        SessionModel,
    )

    async with session_factory() as session:
        sessions = (await session.execute(select(SessionModel))).scalars().all()
    assert len(sessions) == 1
    assert sessions[0].status == "OPEN"


async def _purge_queue(queue_name: str) -> None:
    import aio_pika

    connection = await aio_pika.connect_robust(RABBIT_TEST_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue(queue_name, durable=True)
    await queue.purge()
    await connection.close()
