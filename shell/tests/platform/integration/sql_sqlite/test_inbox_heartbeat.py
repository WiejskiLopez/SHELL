"""Faza 2 tests — heartbeat lease and batch time budget (ref2.md §4.2).

Covers:

- a conditional lease renewal blocks takeover by a second worker;
- the heartbeat keeps the lease fresh while a long handler is running, so a
  concurrent claim does not reclaim the record;
- ``max_batch_time_seconds`` stops processing within a batch once the budget is
  exhausted (remaining claimed records are left to lease expiry).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

import pytest
from sqlalchemy import delete, select

from shell.execution_service.application.execution.task_execution.integration_events.task_execution_created_integration_event import (
    TaskExecutionCreatedIntegrationEvent,
)
from shell.execution_service.domain.execution.aggregates.task_execution.events.task_execution_created_event import (
    TaskExecutionCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.mapping.reflective_integration_mapper import (
    ReflectiveIntegrationMapper,
)
from shell.platform.infrastructure.messaging.event.processor.event_inbox_processor import (
    EventInboxProcessor,
)
from shell.platform.infrastructure.messaging.inbox.inbox_claim_service import InboxClaimService
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


def _event() -> TaskExecutionCreatedIntegrationEvent:
    domain_event = TaskExecutionCreatedEvent.now(
        task_execution_id=TaskExecutionId.generate(),
        now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
    )
    return cast(
        "TaskExecutionCreatedIntegrationEvent",
        ReflectiveIntegrationMapper().map(domain_event),
    )


class SlowBus:
    """Dispatches items after a per-item delay, collecting them."""

    def __init__(self, delay_seconds: float) -> None:
        self._delay = delay_seconds
        self.items: list[object] = []

    async def publish(self, items: Sequence[object]) -> None:
        for item in items:
            await asyncio.sleep(self._delay)
            self.items.append(item)


async def _add_event(
    session_factory: async_sessionmaker,
    event_id: str,
) -> None:
    event = _event()
    serializer = IntegrationEventSerializer()
    async with session_factory() as session:
        session.add(
            _INBOX_MODEL(
                id=event_id,
                outbox_id=f"outbox-{event_id}",
                event_id=event.event_id,
                source_service="execution_service",
                integration_event_name=type(event).__name__,
                occurred_at=event.occurred_at,
                aggregate_id=event.aggregate_id,
                payload=serializer.to_payload(event),
                correlation_id="corr",
                causation_id="cause",
                received_at=datetime.now(tz=UTC),
                status=InboxStatus.PENDING.value,
            )
        )
        await session.commit()


@pytest.fixture(autouse=True)
async def _clean_inbox(session_factory: async_sessionmaker) -> None:
    """Keep the shared module-scoped SQLite DB isolated between tests."""
    async with session_factory() as session:
        await session.execute(delete(_INBOX_MODEL))
        await session.commit()


async def _read_row(
    session_factory: async_sessionmaker,
    event_id: str,
) -> Any:
    async with session_factory() as session:
        row = (
            await session.execute(select(_INBOX_MODEL).where(_INBOX_MODEL.id == event_id))
        ).scalar_one()
        return row


class TestHeartbeatLease:
    async def test_renew_lease_blocks_takeover(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await _add_event(session_factory, "evt-heartbeat")

        worker_a = InboxClaimService(
            session_factory,
            _INBOX_MODEL,
            worker_id="worker-a",
            lease_duration_seconds=5,
        )
        worker_b = InboxClaimService(
            session_factory,
            _INBOX_MODEL,
            worker_id="worker-b",
            lease_duration_seconds=5,
        )

        claimed_a = await worker_a.claim_batch()
        assert len(claimed_a) == 1

        processor = EventInboxProcessor(
            session_factory,
            SlowBus(0.0),
            models=EVENT_DELIVERY_MODELS,
            registry={TaskExecutionCreatedIntegrationEvent.__name__: TaskExecutionCreatedIntegrationEvent},
            worker_id="worker-a",
            lease_duration_seconds=5,
        )
        # Another worker must NOT reclaim while worker A holds a fresh lease.
        assert len(await worker_b.claim_batch()) == 0

        # Renewal extends the lease; a second worker still cannot reclaim.
        renewed = await processor._renew_lease("evt-heartbeat")
        assert renewed is True
        assert len(await worker_b.claim_batch()) == 0

        row = await _read_row(session_factory, "evt-heartbeat")
        assert row.claimed_by == "worker-a"

    async def test_renew_lease_fails_when_record_no_longer_owned(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await _add_event(session_factory, "evt-not-owned")

        processor = EventInboxProcessor(
            session_factory,
            SlowBus(0.0),
            models=EVENT_DELIVERY_MODELS,
            registry={TaskExecutionCreatedIntegrationEvent.__name__: TaskExecutionCreatedIntegrationEvent},
            worker_id="worker-a",
            lease_duration_seconds=5,
        )
        # No one owns the record (PENDING) → renewal touches nothing.
        assert await processor._renew_lease("evt-not-owned") is False

    async def test_heartbeat_keeps_lease_fresh_during_long_handler(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await _add_event(session_factory, "evt-long")

        # The handler is gated so the test never races wall-clock: it starts
        # the handler, waits past the natural lease, then reads the lease.
        # SQLite CURRENT_TIMESTAMP has second granularity, so the lease and the
        # observation window must stay above ~1s (production leases are 60s).
        handler_started = asyncio.Event()
        release_handler = asyncio.Event()

        class GatedBus:
            async def publish(self, items: Sequence[object]) -> None:
                handler_started.set()
                await release_handler.wait()

        processor = EventInboxProcessor(
            session_factory,
            GatedBus(),
            models=EVENT_DELIVERY_MODELS,
            registry={TaskExecutionCreatedIntegrationEvent.__name__: TaskExecutionCreatedIntegrationEvent},
            worker_id="worker-a",
            lease_duration_seconds=3,
            heartbeat_interval_seconds=0.5,
        )

        result_task = asyncio.create_task(processor.run_once())
        await handler_started.wait()

        # Natural lease (3s) expired well before this point; only the heartbeat
        # can keep the record owned by worker-a.
        await asyncio.sleep(3.5)
        async with session_factory() as session:
            row = (
                await session.execute(select(_INBOX_MODEL).where(_INBOX_MODEL.id == "evt-long"))
            ).scalar_one()
            assert row.status == InboxStatus.PROCESSING.value
            assert row.claimed_by == "worker-a"
            assert row.lease_until is not None
            lease_until = row.lease_until
            if lease_until.tzinfo is None:
                lease_until = lease_until.replace(tzinfo=UTC)
            assert lease_until > datetime.now(tz=UTC)

        release_handler.set()
        result = await result_task
        assert result.processed_count == 1
        row = await _read_row(session_factory, "evt-long")
        assert row.status == InboxStatus.PROCESSED.value

    async def test_lease_lost_during_processing_prevents_ack(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        """When the heartbeat detects a lost lease, the handler result is not acked.

        Another worker reclaims the record mid-handler; the heartbeat renewal
        touches zero rows, so worker-a must neither ack nor schedule a retry
        (the record now belongs to worker-b).
        """
        await _add_event(session_factory, "evt-leaselost")

        handler_started = asyncio.Event()
        release_handler = asyncio.Event()

        class GatedBus:
            async def publish(self, items: Sequence[object]) -> None:
                handler_started.set()
                await release_handler.wait()

        processor = EventInboxProcessor(
            session_factory,
            GatedBus(),
            models=EVENT_DELIVERY_MODELS,
            registry={TaskExecutionCreatedIntegrationEvent.__name__: TaskExecutionCreatedIntegrationEvent},
            worker_id="worker-a",
            lease_duration_seconds=5,
            heartbeat_interval_seconds=0.1,
        )

        result_task = asyncio.create_task(processor.run_once())
        await handler_started.wait()

        # Simulate an expired-lease reclaim by another worker.
        async with session_factory() as session:
            row = (
                await session.execute(
                    select(_INBOX_MODEL).where(_INBOX_MODEL.id == "evt-leaselost")
                )
            ).scalar_one()
            row.claimed_by = "worker-b"
            await session.commit()

        release_handler.set()
        result = await result_task

        assert result.failed_count == 1
        row = await _read_row(session_factory, "evt-leaselost")
        assert row.status == InboxStatus.PROCESSING.value
        assert row.claimed_by == "worker-b", "worker-a must not ack a record it no longer owns"

    async def test_without_heartbeat_batch_is_capped_to_one(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        """Without a heartbeat the worker cannot renew leases, so a batch is capped at one."""
        await _add_event(session_factory, "evt-single-a")
        await _add_event(session_factory, "evt-single-b")

        processor = EventInboxProcessor(
            session_factory,
            SlowBus(0.0),
            models=EVENT_DELIVERY_MODELS,
            registry={TaskExecutionCreatedIntegrationEvent.__name__: TaskExecutionCreatedIntegrationEvent},
            worker_id="worker-a",
            lease_duration_seconds=5,
        )
        result = await processor.run_once()

        assert result.claimed_count == 1
        assert result.processed_count == 1
        row_b = await _read_row(session_factory, "evt-single-b")
        assert row_b.status == InboxStatus.PENDING.value, "second record must not be claimed"


class TestMaxBatchTime:
    async def test_batch_time_budget_stops_processing(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await _add_event(session_factory, "evt-batch-a")
        await _add_event(session_factory, "evt-batch-b")

        processor = EventInboxProcessor(
            session_factory,
            SlowBus(0.15),
            models=EVENT_DELIVERY_MODELS,
            registry={TaskExecutionCreatedIntegrationEvent.__name__: TaskExecutionCreatedIntegrationEvent},
            worker_id="worker-a",
            lease_duration_seconds=5,
            heartbeat_interval_seconds=10,
            max_batch_time_seconds=0.05,
        )

        result = await processor.run_once()

        assert result.claimed_count == 2
        assert result.processed_count == 1
        row_b = await _read_row(session_factory, "evt-batch-b")
        assert row_b.status == InboxStatus.PROCESSING.value
        assert row_b.claimed_by == "worker-a"

    async def test_no_budget_uses_default_batch_time(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await _add_event(session_factory, "evt-batch-c")

        processor = EventInboxProcessor(
            session_factory,
            SlowBus(0.0),
            models=EVENT_DELIVERY_MODELS,
            registry={TaskExecutionCreatedIntegrationEvent.__name__: TaskExecutionCreatedIntegrationEvent},
            worker_id="worker-a",
            lease_duration_seconds=5,
        )
        result = await processor.run_once()
        assert result.claimed_count == 1
        assert result.processed_count == 1
