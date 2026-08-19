"""SQLite integration tests for OutboxToTransportRelay (producer-side bridge)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from shell.execution_service.domain.execution.aggregates.task_execution.events.task_execution_created_event import (
    TaskExecutionCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.messaging.event.sql_event_outbox_publisher import (
    SqlEventOutboxPublisher,
)
from shell.platform.infrastructure.messaging.transport import OutboxToTransportRelay
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.tests.platform.integration.platform_delivery_models import (
    EVENT_DELIVERY_MODELS,
)

if TYPE_CHECKING:
    from shell.platform.application.ports.transport.delivery_transport import DeliveryEnvelope

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_OUTBOX_MODEL: Any = EVENT_DELIVERY_MODELS.outbox


class RecordingTransport:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.delivered: list[DeliveryEnvelope] = []

    async def deliver(self, envelope: DeliveryEnvelope) -> None:
        if self.fail:
            raise RuntimeError("broker unavailable")
        self.delivered.append(envelope)


class FlakyTimeoutTransport:
    """Fails the first delivery with a timeout, then succeeds (retry test)."""

    def __init__(self) -> None:
        self.attempts = 0
        self.delivered: list[DeliveryEnvelope] = []

    async def deliver(self, envelope: DeliveryEnvelope) -> None:
        self.attempts += 1
        if self.attempts == 1:
            raise TimeoutError("broker timed out")
        self.delivered.append(envelope)


class AcceptedThenTimeoutTransport:
    """Records broker acceptance before the producer observes a timeout."""

    def __init__(self) -> None:
        self.attempts = 0
        self.delivered: list[DeliveryEnvelope] = []

    async def deliver(self, envelope: DeliveryEnvelope) -> None:
        self.attempts += 1
        self.delivered.append(envelope)
        if self.attempts == 1:
            raise TimeoutError("broker response was lost")


class TestOutboxToTransportRelay:
    async def test_delivers_pending_and_marks_published(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await SqlEventOutboxPublisher(session_factory, EVENT_DELIVERY_MODELS).publish(
            [
                TaskExecutionCreatedEvent.now(
                    task_execution_id=TaskExecutionId.generate(),
                    now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
                )
            ]
        )

        transport = RecordingTransport()
        relay = OutboxToTransportRelay(
            session_factory, EVENT_DELIVERY_MODELS, transport, kind="event"
        )
        count = await relay.run_once()

        assert count == 1
        assert len(transport.delivered) == 1
        assert transport.delivered[0].kind == "event"
        assert transport.delivered[0].delivery_type == "TaskExecutionCreatedEvent"
        assert transport.delivered[0].payload == transport.delivered[0].payload

        async with session_factory() as session:
            rows = (
                (
                    await session.execute(
                        select(_OUTBOX_MODEL).where(_OUTBOX_MODEL.published_at.is_(None))
                    )
                )
                .scalars()
                .all()
            )
        assert rows == []

    async def test_does_not_mark_published_when_transport_fails(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        url = f"sqlite+aiosqlite:///{tmp_path / 'relay-fail.db'}"
        engine = create_async_engine(url)
        async with engine.begin() as connection:
            await connection.run_sync(EVENT_DELIVERY_MODELS.outbox.metadata.create_all)
        await engine.dispose()
        isolated = build_session_factory(url)

        await SqlEventOutboxPublisher(isolated, EVENT_DELIVERY_MODELS).publish(
            [
                TaskExecutionCreatedEvent.now(
                    task_execution_id=TaskExecutionId.generate(),
                    now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
                )
            ]
        )

        relay = OutboxToTransportRelay(
            isolated,
            EVENT_DELIVERY_MODELS,
            RecordingTransport(fail=True),
            kind="event",
        )
        try:
            await relay.run_once()
        except RuntimeError:
            pass
        else:
            raise AssertionError("expected RuntimeError from transport")

        async with isolated() as session:
            rows = (await session.execute(select(_OUTBOX_MODEL))).scalars().all()
        assert len(rows) == 1
        assert rows[0].published_at is None

    async def test_timeout_is_retried_and_never_marks_published(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        """A broker timeout must not lose the outbox row or mark it published."""
        url = f"sqlite+aiosqlite:///{tmp_path / 'relay-timeout.db'}"
        engine = create_async_engine(url)
        async with engine.begin() as connection:
            await connection.run_sync(EVENT_DELIVERY_MODELS.outbox.metadata.create_all)
        await engine.dispose()
        isolated = build_session_factory(url)

        await SqlEventOutboxPublisher(isolated, EVENT_DELIVERY_MODELS).publish(
            [
                TaskExecutionCreatedEvent.now(
                    task_execution_id=TaskExecutionId.generate(),
                    now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
                )
            ]
        )

        transport = FlakyTimeoutTransport()
        relay = OutboxToTransportRelay(
            isolated,
            EVENT_DELIVERY_MODELS,
            transport,
            kind="event",
        )

        # First attempt times out: the outbox row is left unpublished.
        with pytest.raises(TimeoutError):
            await relay.run_once()

        async with isolated() as session:
            rows = (await session.execute(select(_OUTBOX_MODEL))).scalars().all()
        assert len(rows) == 1
        assert rows[0].published_at is None

        # Retry succeeds: the record is delivered exactly once and marked published.
        count = await relay.run_once()
        assert count == 1
        assert len(transport.delivered) == 1
        async with isolated() as session:
            rows = (await session.execute(select(_OUTBOX_MODEL))).scalars().all()
        assert rows[0].published_at is not None

    async def test_ambiguous_transport_result_keeps_at_least_once_delivery(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        url = f"sqlite+aiosqlite:///{tmp_path / 'relay-ambiguous.db'}"
        engine = create_async_engine(url)
        async with engine.begin() as connection:
            await connection.run_sync(EVENT_DELIVERY_MODELS.outbox.metadata.create_all)
        await engine.dispose()
        isolated = build_session_factory(url)

        await SqlEventOutboxPublisher(isolated, EVENT_DELIVERY_MODELS).publish(
            [
                TaskExecutionCreatedEvent.now(
                    task_execution_id=TaskExecutionId.generate(),
                    now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
                )
            ]
        )

        transport = AcceptedThenTimeoutTransport()
        relay = OutboxToTransportRelay(
            isolated,
            EVENT_DELIVERY_MODELS,
            transport,
            kind="event",
        )

        with pytest.raises(TimeoutError):
            await relay.run_once()

        async with isolated() as session:
            row = (await session.execute(select(_OUTBOX_MODEL))).scalar_one()
            assert row.published_at is None

        assert len(transport.delivered) == 1
        assert await relay.run_once() == 1
        assert len(transport.delivered) == 2

        async with isolated() as session:
            row = (await session.execute(select(_OUTBOX_MODEL))).scalar_one()
            assert row.published_at is not None
