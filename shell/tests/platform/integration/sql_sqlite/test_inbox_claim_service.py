"""SQLite integration tests for InboxClaimService claim/lease semantics."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import select

from shell.definition.infrastructure.definition.persistence.sql.models.base import (
    EVENT_DELIVERY_MODELS,
)
from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.infrastructure.messaging.inbox import InboxClaimService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.platform.infrastructure.messaging.inbox.inbox_claim_service import InboxStateModel

_INBOX_MODEL: type[InboxStateModel] = cast("type[InboxStateModel]", EVENT_DELIVERY_MODELS.inbox)


async def _add_event(
    session_factory: async_sessionmaker,
    event_id: str,
    *,
    status: str = InboxStatus.PENDING.value,
    next_attempt_at: datetime | None = None,
    lease_until: datetime | None = None,
    claimed_by: str | None = None,
) -> None:
    now = datetime.now(tz=UTC)
    async with session_factory() as session:
        session.add(
            EVENT_DELIVERY_MODELS.inbox(
                id=event_id,
                event_type="SampleEvent",
                occurred_at=now,
                payload={},
                correlation_id="corr",
                causation_id="cause",
                received_at=now,
                status=status,
                next_attempt_at=next_attempt_at or now - timedelta(hours=1),
                lease_until=lease_until,
                claimed_by=claimed_by,
            )
        )
        await session.commit()


async def _read_status(
    session_factory: async_sessionmaker,
    event_id: str,
) -> Any:
    async with session_factory() as session:
        row = (
            await session.execute(select(_INBOX_MODEL).where(_INBOX_MODEL.id == event_id))
        ).scalar_one()
        return row


class TestInboxClaimService:
    async def test_claims_pending_records(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await _add_event(session_factory, "event-pending")
        service = InboxClaimService(
            session_factory,
            _INBOX_MODEL,
            worker_id="worker-1",
            lease_duration_seconds=30,
        )
        claimed = await service.claim_batch()
        assert len(claimed) == 1

        row = await _read_status(session_factory, "event-pending")
        assert row.status == InboxStatus.PROCESSING.value
        assert row.claimed_by == "worker-1"
        assert row.lease_until is not None

    async def test_does_not_claim_record_in_processing_with_active_lease(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        now = datetime.now(tz=UTC)
        await _add_event(
            session_factory,
            "event-active",
            status=InboxStatus.PROCESSING.value,
            lease_until=now + timedelta(minutes=5),
            claimed_by="worker-other",
        )
        service = InboxClaimService(
            session_factory,
            _INBOX_MODEL,
            worker_id="worker-1",
            lease_duration_seconds=30,
        )
        claimed = await service.claim_batch()
        assert claimed == []

    async def test_reclaims_expired_lease(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        now = datetime.now(tz=UTC)
        await _add_event(
            session_factory,
            "event-expired",
            status=InboxStatus.PROCESSING.value,
            lease_until=now - timedelta(minutes=5),
            claimed_by="worker-dead",
        )
        service = InboxClaimService(
            session_factory,
            _INBOX_MODEL,
            worker_id="worker-1",
            lease_duration_seconds=30,
        )
        claimed = await service.claim_batch()
        assert len(claimed) == 1

        row = await _read_status(session_factory, "event-expired")
        assert row.status == InboxStatus.PROCESSING.value
        assert row.claimed_by == "worker-1"

    async def test_does_not_claim_retry_before_next_attempt_at(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await _add_event(
            session_factory,
            "event-not-due",
            status=InboxStatus.RETRY.value,
            next_attempt_at=datetime.now(tz=UTC) + timedelta(minutes=30),
        )
        service = InboxClaimService(
            session_factory,
            _INBOX_MODEL,
            worker_id="worker-1",
            lease_duration_seconds=30,
        )
        claimed = await service.claim_batch()
        assert claimed == []

    async def test_claims_retry_after_next_attempt_at(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await _add_event(
            session_factory,
            "event-due",
            status=InboxStatus.RETRY.value,
            next_attempt_at=datetime.now(tz=UTC) - timedelta(minutes=1),
        )
        service = InboxClaimService(
            session_factory,
            _INBOX_MODEL,
            worker_id="worker-1",
            lease_duration_seconds=30,
        )
        claimed = await service.claim_batch()
        assert len(claimed) == 1

    async def test_two_workers_do_not_claim_same_record(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await _add_event(session_factory, "event-contended")
        first = InboxClaimService(
            session_factory,
            _INBOX_MODEL,
            worker_id="worker-1",
            lease_duration_seconds=30,
        )
        second = InboxClaimService(
            session_factory,
            _INBOX_MODEL,
            worker_id="worker-2",
            lease_duration_seconds=30,
        )
        assert len(await first.claim_batch()) == 1
        assert await second.claim_batch() == []
