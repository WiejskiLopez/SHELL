"""SQLite integration tests for InboxReplayService exclusivity and reset semantics."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.infrastructure.messaging.inbox import InboxReplayService
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.tests.platform.integration.platform_delivery_models import (
    EVENT_DELIVERY_MODELS,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.platform.infrastructure.messaging.inbox.inbox_claim_service import InboxStateModel

_INBOX_MODEL: type[InboxStateModel] = cast("type[InboxStateModel]", EVENT_DELIVERY_MODELS.inbox)


async def _add_event(
    session_factory: async_sessionmaker,
    event_id: str,
    *,
    status: str,
    retry_count: int = 0,
    lease_until: datetime | None = None,
    claimed_by: str | None = None,
    error_code: str | None = None,
) -> None:
    async with session_factory() as session:
        session.add(
            EVENT_DELIVERY_MODELS.inbox(
                id=event_id,
                event_id=event_id,
                source_service="execution_service",
                integration_event_name="SampleEvent",
                occurred_at=datetime.now(tz=UTC),
                aggregate_id="aggregate-1",
                payload={"k": "v"},
                correlation_id="corr",
                causation_id="cause",
                received_at=datetime.now(tz=UTC),
                status=status,
                retry_count=retry_count,
                lease_until=lease_until,
                claimed_by=claimed_by,
                error_code=error_code,
            )
        )
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


class TestInboxReplayService:
    async def test_replays_dead_letter_record(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await _add_event(
            session_factory,
            "dlq-1",
            status=InboxStatus.DEAD_LETTER.value,
            retry_count=3,
            error_code="HANDLER_ERROR",
        )
        service = InboxReplayService(session_factory, _INBOX_MODEL)
        assert await service.replay_by_id("dlq-1", operator="ops", reason="fixed bug") is True

        row = await _read_row(session_factory, "dlq-1")
        assert row.status == InboxStatus.PENDING.value
        assert row.retry_count == 0
        assert row.error_code is None
        assert row.payload == {"k": "v"}
        assert row.claimed_by is None
        assert row.lease_until is None

    async def test_does_not_replay_active_lease(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await _add_event(
            session_factory,
            "active-1",
            status=InboxStatus.PROCESSING.value,
            lease_until=datetime.now(tz=UTC) + timedelta(minutes=5),
            claimed_by="worker-live",
        )
        service = InboxReplayService(session_factory, _INBOX_MODEL)
        assert await service.replay_by_id("active-1", operator="ops", reason="why") is False

        row = await _read_row(session_factory, "active-1")
        assert row.status == InboxStatus.PROCESSING.value
        assert row.claimed_by == "worker-live"

    async def test_parallel_replay_cannot_reset_active_lease(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        """Concurrent replay attempts must never reset a record with a valid lease."""
        await _add_event(
            session_factory,
            "active-par",
            status=InboxStatus.PROCESSING.value,
            lease_until=datetime.now(tz=UTC) + timedelta(minutes=5),
            claimed_by="worker-live",
        )
        service = InboxReplayService(session_factory, _INBOX_MODEL)

        results = await asyncio.gather(
            service.replay_by_id("active-par", operator="ops-a", reason="r1"),
            service.replay_by_id("active-par", operator="ops-b", reason="r2"),
        )

        assert len(results) == 2
        assert all(result is False for result in results)
        row = await _read_row(session_factory, "active-par")
        assert row.status == InboxStatus.PROCESSING.value
        assert row.claimed_by == "worker-live"
        assert row.lease_until is not None

    async def test_replays_expired_lease(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await _add_event(
            session_factory,
            "stale-1",
            status=InboxStatus.PROCESSING.value,
            lease_until=datetime.now(tz=UTC) - timedelta(minutes=5),
            claimed_by="worker-dead",
        )
        service = InboxReplayService(session_factory, _INBOX_MODEL)
        assert await service.replay_by_id("stale-1", operator="ops", reason="recover") is True

        row = await _read_row(session_factory, "stale-1")
        assert row.status == InboxStatus.PENDING.value
        assert row.claimed_by is None

    async def test_replays_all_dead_lettered(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        url = f"sqlite+aiosqlite:///{tmp_path / 'replay-dlq.db'}"
        engine = create_async_engine(url)
        async with engine.begin() as connection:
            await connection.run_sync(EVENT_DELIVERY_MODELS.inbox.metadata.create_all)
        await engine.dispose()
        isolated = build_session_factory(url)

        await _add_event(isolated, "dlq-a", status=InboxStatus.DEAD_LETTER.value)
        await _add_event(isolated, "dlq-b", status=InboxStatus.DEAD_LETTER.value)
        await _add_event(isolated, "ok-a", status=InboxStatus.PROCESSED.value)

        service = InboxReplayService(isolated, _INBOX_MODEL)
        count = await service.replay_dead_lettered(operator="ops", reason="retry batch")
        assert count == 2

        assert (await _read_row(isolated, "dlq-a")).status == InboxStatus.PENDING.value
        assert (await _read_row(isolated, "dlq-b")).status == InboxStatus.PENDING.value
        assert (await _read_row(isolated, "ok-a")).status == InboxStatus.PROCESSED.value

    async def test_replays_all_processed(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        url = f"sqlite+aiosqlite:///{tmp_path / 'replay-processed.db'}"
        engine = create_async_engine(url)
        async with engine.begin() as connection:
            await connection.run_sync(EVENT_DELIVERY_MODELS.inbox.metadata.create_all)
        await engine.dispose()
        isolated = build_session_factory(url)

        await _add_event(isolated, "p-a", status=InboxStatus.PROCESSED.value)
        await _add_event(isolated, "p-b", status=InboxStatus.PROCESSED.value)

        service = InboxReplayService(isolated, _INBOX_MODEL)
        count = await service.replay_processed(operator="ops", reason="recompute")
        assert count == 2
        assert (await _read_row(isolated, "p-a")).status == InboxStatus.PENDING.value
