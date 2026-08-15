"""PostgreSQL integration tests — claim/lease concurrency (FOR UPDATE SKIP LOCKED)."""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

import pytest
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

PG_TEST_URL = os.environ.get("POSTGRES_TEST_URL")
skip_no_postgres = pytest.mark.skipif(
    PG_TEST_URL is None,
    reason="POSTGRES_TEST_URL not set — start docker-compose.test.yml to enable",
)


async def _clear_inbox(session_factory: async_sessionmaker) -> None:
    from sqlalchemy import delete

    async with session_factory() as session:
        await session.execute(delete(EVENT_DELIVERY_MODELS.inbox))
        await session.commit()


@skip_no_postgres
async def test_two_workers_do_not_claim_same_record(
    pg_session_factory: async_sessionmaker,
) -> None:
    await _clear_inbox(pg_session_factory)
    delivery_id = f"pg-claim-{uuid.uuid4().hex}"
    now = datetime.now(tz=UTC)
    async with pg_session_factory() as session:
        session.add(
            EVENT_DELIVERY_MODELS.inbox(
                id=delivery_id,
                event_type="SampleEvent",
                occurred_at=now,
                payload={},
                correlation_id="c",
                causation_id="k",
                received_at=now,
                status=InboxStatus.PENDING.value,
            )
        )
        await session.commit()

    worker_a = InboxClaimService(
        pg_session_factory,
        _INBOX_MODEL,
        worker_id="worker-a",
        lease_duration_seconds=30,
    )
    worker_b = InboxClaimService(
        pg_session_factory,
        _INBOX_MODEL,
        worker_id="worker-b",
        lease_duration_seconds=30,
    )

    # Both workers race; SKIP LOCKED ensures only one claims the single row.
    a_claimed, b_claimed = await asyncio.gather(
        worker_a.claim_batch(),
        worker_b.claim_batch(),
    )
    assert (len(a_claimed), len(b_claimed)) in ((1, 0), (0, 1))

    async with pg_session_factory() as session:
        row = (
            await session.execute(select(_INBOX_MODEL).where(_INBOX_MODEL.id == delivery_id))
        ).scalar_one()
    assert row.status == InboxStatus.PROCESSING.value
    assert row.claimed_by in ("worker-a", "worker-b")


@skip_no_postgres
async def test_expired_lease_is_reclaimed_by_other_worker(
    pg_session_factory: async_sessionmaker,
) -> None:
    delivery_id = f"pg-stale-{uuid.uuid4().hex}"
    now = datetime.now(tz=UTC)
    async with pg_session_factory() as session:
        session.add(
            EVENT_DELIVERY_MODELS.inbox(
                id=delivery_id,
                event_type="SampleEvent",
                occurred_at=now,
                payload={},
                correlation_id="c",
                causation_id="k",
                received_at=now,
                status=InboxStatus.PROCESSING.value,
                claimed_by="dead-worker",
                lease_until=now,
            )
        )
        await session.commit()

    worker = InboxClaimService(
        pg_session_factory,
        _INBOX_MODEL,
        worker_id="worker-b",
        lease_duration_seconds=30,
    )
    claimed = await worker.claim_batch()
    assert len(claimed) == 1

    async with pg_session_factory() as session:
        row = (
            await session.execute(select(_INBOX_MODEL).where(_INBOX_MODEL.id == delivery_id))
        ).scalar_one()
    assert row.claimed_by == "worker-b"
