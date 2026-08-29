"""SQLite integration tests for OutboxToTransportRelay (producer-side bridge)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from shell.execution_service.application.execution.task_execution.integration_events.task_execution_created_integration_event import (
    TaskExecutionCreatedIntegrationEvent,
)
from shell.platform.infrastructure.messaging.transport import OutboxToTransportRelay
from shell.platform.infrastructure.messaging.transport.source_service import (
    source_service_for_type,
)
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.serialization.event.integration_event_serializer import (
    IntegrationEventSerializer,
)
from shell.tests.platform.integration.platform_delivery_models import (
    EVENT_DELIVERY_MODELS,
)

if TYPE_CHECKING:
    from shell.platform.application.ports.transport.delivery_transport import DeliveryEnvelope

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_OUTBOX_MODEL: Any = EVENT_DELIVERY_MODELS.outbox


async def _seed_outbox(session_factory: async_sessionmaker) -> None:
    event = TaskExecutionCreatedIntegrationEvent(
        event_id="event-1",
        correlation_id="correlation-1",
        causation_id="causation-1",
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        aggregate_id="task-execution-1",
        aggregate_name="TaskExecution",
        schema_version=1,
        task_execution_id="task-execution-1",
    )
    envelope = IntegrationEventSerializer().to_envelope(
        event,
        outbox_id="outbox-1",
        source_service=source_service_for_type(type(event)),
    )
    async with session_factory() as session:
        session.add(
            _OUTBOX_MODEL(
                id=envelope["outbox_id"],
                event_id=envelope["event_id"],
                source_service=envelope["source_service"],
                event_type=envelope["event_type"],
                occurred_at=envelope["occurred_at"],
                aggregate_id=envelope["aggregate_id"],
                aggregate_name=envelope["aggregate_name"],
                schema_version=envelope["schema_version"],
                payload=envelope["payload"],
                correlation_id=envelope["correlation_id"],
                causation_id=envelope["causation_id"],
            )
        )
        await session.commit()


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


class UnroutableThenRoutableTransport:
    """Fails with an unroutable publish error until a binding is added."""

    def __init__(self) -> None:
        self.attempts = 0
        self.delivered: list[DeliveryEnvelope] = []

    async def deliver(self, envelope: DeliveryEnvelope) -> None:
        self.attempts += 1
        if self.attempts == 1:
            raise RuntimeError("NO_ROUTE: unroutable message (binding missing)")
        self.delivered.append(envelope)


class TestOutboxToTransportRelay:
    async def test_delivers_pending_and_marks_published(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await _seed_outbox(session_factory)

        transport = RecordingTransport()
        relay = OutboxToTransportRelay(
            session_factory, EVENT_DELIVERY_MODELS, transport, kind="event"
        )
        count = await relay.run_once()

        assert count == 1
        assert len(transport.delivered) == 1
        assert transport.delivered[0].kind == "event"
        assert transport.delivered[0].contract_type == "TaskExecutionCreatedIntegrationEvent"
        assert transport.delivered[0].event_id is not None
        assert transport.delivered[0].schema_version == 1
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

        await _seed_outbox(isolated)

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

        await _seed_outbox(isolated)

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

        await _seed_outbox(isolated)

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

    async def test_unroutable_error_is_retried_after_binding_added(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        """An unroutable publish (no binding) must not mark the record,
        and the relay must deliver it once the binding exists (retry)."""
        url = f"sqlite+aiosqlite:///{tmp_path / 'relay-unroutable.db'}"
        engine = create_async_engine(url)
        async with engine.begin() as connection:
            await connection.run_sync(EVENT_DELIVERY_MODELS.outbox.metadata.create_all)
        await engine.dispose()
        isolated = build_session_factory(url)

        await _seed_outbox(isolated)

        transport = UnroutableThenRoutableTransport()
        relay = OutboxToTransportRelay(
            isolated,
            EVENT_DELIVERY_MODELS,
            transport,
            kind="event",
        )

        with pytest.raises(RuntimeError, match="NO_ROUTE"):
            await relay.run_once()

        async with isolated() as session:
            rows = (await session.execute(select(_OUTBOX_MODEL))).scalars().all()
        assert len(rows) == 1
        assert rows[0].published_at is None

        count = await relay.run_once()
        assert count == 1
        assert len(transport.delivered) == 1

        async with isolated() as session:
            rows = (await session.execute(select(_OUTBOX_MODEL))).scalars().all()
        assert rows[0].published_at is not None
