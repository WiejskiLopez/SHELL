"""SQLite integration tests for InboxMetricsService backlog snapshot."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, cast

from shell.definition.infrastructure.definition.persistence.sql.models.base import (
    EVENT_DELIVERY_MODELS,
)
from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.infrastructure.messaging.inbox import InboxMetricsService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.platform.infrastructure.messaging.inbox.inbox_claim_service import InboxStateModel

_INBOX_MODEL: type[InboxStateModel] = cast("type[InboxStateModel]", EVENT_DELIVERY_MODELS.inbox)


async def _add_event(
    session_factory: async_sessionmaker,
    event_id: str,
    *,
    status: str,
    received_at: datetime | None = None,
) -> None:
    async with session_factory() as session:
        session.add(
            EVENT_DELIVERY_MODELS.inbox(
                id=event_id,
                event_type="SampleEvent",
                occurred_at=datetime.now(tz=UTC),
                payload={},
                correlation_id="c",
                causation_id="k",
                received_at=received_at or datetime.now(tz=UTC),
                status=status,
            )
        )
        await session.commit()


class TestInboxMetricsService:
    async def test_snapshot_counts_by_status(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await _add_event(session_factory, "m-pending", status=InboxStatus.PENDING.value)
        await _add_event(session_factory, "m-pending2", status=InboxStatus.PENDING.value)
        await _add_event(session_factory, "m-retry", status=InboxStatus.RETRY.value)
        await _add_event(session_factory, "m-dlq", status=InboxStatus.DEAD_LETTER.value)

        service = InboxMetricsService(session_factory, _INBOX_MODEL)
        snapshot = await service.snapshot()

        assert snapshot.pending == 2
        assert snapshot.retry == 1
        assert snapshot.dead_letter == 1
        assert snapshot.total == 4

    async def test_snapshot_reports_oldest_pending_age(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        old = datetime.now(tz=UTC) - timedelta(minutes=10)
        await _add_event(
            session_factory,
            "m-old",
            status=InboxStatus.PENDING.value,
            received_at=old,
        )

        service = InboxMetricsService(session_factory, _INBOX_MODEL)
        snapshot = await service.snapshot()

        assert snapshot.pending >= 1
        assert snapshot.oldest_pending_age_seconds is not None
        assert snapshot.oldest_pending_age_seconds >= 540.0  # >= 9 minutes
