"""Faza 5 tests — DeliveryRetentionService (DLQ + processed_delivery retention)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from shell.definition.infrastructure.definition.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
)
from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.infrastructure.messaging.inbox.delivery_retention_service import (
    DeliveryRetentionService,
)
from shell.platform.infrastructure.persistence.sql import build_session_factory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_INBOX_MODEL: Any = PERSISTENCE_DELIVERY_MODELS.events.inbox
_PROCESSED_DELIVERY_MODEL: Any = PERSISTENCE_DELIVERY_MODELS.processed_delivery


async def _build_isolated(tmp_path) -> async_sessionmaker:
    url = f"sqlite+aiosqlite:///{tmp_path / 'retention.db'}"
    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.run_sync(PERSISTENCE_DELIVERY_MODELS.events.inbox.metadata.create_all)
    await engine.dispose()
    return build_session_factory(url)


async def _seed_inbox(
    session_factory: async_sessionmaker,
    record_id: str,
    *,
    failed_at: datetime,
) -> None:
    async with session_factory() as session:
        session.add(
            PERSISTENCE_DELIVERY_MODELS.events.inbox(
                id=record_id,
                event_type="SomeEvent",
                occurred_at=datetime.now(tz=UTC),
                payload={},
                correlation_id="c",
                causation_id="k",
                received_at=failed_at,
                failed_at=failed_at,
                status=InboxStatus.DEAD_LETTER.value,
            )
        )
        await session.commit()


async def _seed_processed_delivery(
    session_factory: async_sessionmaker,
    delivery_id: str,
    *,
    processed_at: datetime,
) -> None:
    async with session_factory() as session:
        session.add(
            PERSISTENCE_DELIVERY_MODELS.processed_delivery(
                id=str(uuid4()),
                consumer_name="test-consumer",
                delivery_id=delivery_id,
                payload={},
                processed_at=processed_at,
            )
        )
        await session.commit()


async def _inbox_ids(session_factory: async_sessionmaker) -> set[str]:
    async with session_factory() as session:
        rows = (await session.execute(select(_INBOX_MODEL.id))).scalars().all()
        return set(rows)


async def _processed_ids(session_factory: async_sessionmaker) -> set[str]:
    async with session_factory() as session:
        rows = (
            (await session.execute(select(_PROCESSED_DELIVERY_MODEL.delivery_id))).scalars().all()
        )
        return set(rows)


class TestDeliveryRetentionService:
    async def test_purges_old_dlq_and_dedup_keeps_recent(
        self,
        tmp_path,
    ) -> None:
        session_factory = await _build_isolated(tmp_path)
        now = datetime(2026, 8, 15, tzinfo=UTC)

        await _seed_inbox(
            session_factory,
            "dlq-old",
            failed_at=now - timedelta(days=400),
        )
        await _seed_inbox(
            session_factory,
            "dlq-recent",
            failed_at=now - timedelta(days=10),
        )
        await _seed_processed_delivery(
            session_factory,
            "dedup-old",
            processed_at=now - timedelta(days=400),
        )
        await _seed_processed_delivery(
            session_factory,
            "dedup-recent",
            processed_at=now - timedelta(days=10),
        )

        service = DeliveryRetentionService(
            session_factory,
            _INBOX_MODEL,
            _PROCESSED_DELIVERY_MODEL,
            dead_letter_retention_days=90,
            processed_delivery_retention_days=30,
            now=now,
        )
        report = await service.purge_expired()

        assert report.purged_dead_letter == 1
        assert report.purged_processed_delivery == 1
        assert await _inbox_ids(session_factory) == {"dlq-recent"}
        assert await _processed_ids(session_factory) == {"dedup-recent"}

    async def test_no_rows_is_noop(
        self,
        tmp_path,
    ) -> None:
        session_factory = await _build_isolated(tmp_path)
        service = DeliveryRetentionService(
            session_factory,
            _INBOX_MODEL,
            _PROCESSED_DELIVERY_MODEL,
            now=datetime(2026, 8, 15, tzinfo=UTC),
        )
        report = await service.purge_expired()

        assert report.purged_dead_letter == 0
        assert report.purged_processed_delivery == 0

    async def test_non_dlq_rows_are_never_purged(
        self,
        tmp_path,
    ) -> None:
        session_factory = await _build_isolated(tmp_path)
        now = datetime(2026, 8, 15, tzinfo=UTC)
        async with session_factory() as session:
            session.add(
                PERSISTENCE_DELIVERY_MODELS.events.inbox(
                    id="pending-old",
                    event_type="SomeEvent",
                    occurred_at=now,
                    payload={},
                    correlation_id="c",
                    causation_id="k",
                    received_at=now - timedelta(days=400),
                    status=InboxStatus.PENDING.value,
                )
            )
            await session.commit()

        service = DeliveryRetentionService(
            session_factory,
            _INBOX_MODEL,
            _PROCESSED_DELIVERY_MODEL,
            dead_letter_retention_days=90,
            now=now,
        )
        await service.purge_expired()

        assert await _inbox_ids(session_factory) == {"pending-old"}


class TestRetentionCli:
    async def test_purge_for_bc_runs_retention_for_a_bounded_context(
        self,
        tmp_path,
    ) -> None:
        from shell.platform.infrastructure.cli.retention import (
            purge_for_bounded_context,
        )

        # The CLI loads the definition BC persistence models and its own URL.
        url = f"sqlite+aiosqlite:///{tmp_path / 'retention-cli.db'}"
        engine = create_async_engine(url)
        async with engine.begin() as connection:
            await connection.run_sync(PERSISTENCE_DELIVERY_MODELS.events.inbox.metadata.create_all)
            await connection.run_sync(
                PERSISTENCE_DELIVERY_MODELS.processed_delivery.metadata.create_all
            )
        await engine.dispose()
        session_factory = build_session_factory(url)

        now = datetime.now(tz=UTC)
        await _seed_inbox(
            session_factory,
            "dlq-old-cli",
            failed_at=now - timedelta(days=400),
        )
        await _seed_processed_delivery(
            session_factory,
            "dedup-old-cli",
            processed_at=now - timedelta(days=400),
        )

        report = await purge_for_bounded_context(
            "definition",
            url,
            dead_letter_retention_days=90,
            processed_delivery_retention_days=30,
        )

        assert report.purged_dead_letter == 1
        assert report.purged_processed_delivery == 1
