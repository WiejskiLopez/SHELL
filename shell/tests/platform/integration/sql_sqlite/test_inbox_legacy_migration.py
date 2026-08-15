"""SQLite integration tests — InboxLegacyMigration deterministic classification."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from shell.definition.infrastructure.definition.persistence.sql.models.base import (
    EVENT_DELIVERY_MODELS,
)
from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.infrastructure.messaging.inbox import InboxLegacyMigration
from shell.platform.infrastructure.persistence.sql import build_session_factory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_INBOX_MODEL: Any = EVENT_DELIVERY_MODELS.inbox


async def _add_legacy(
    session_factory: async_sessionmaker,
    event_id: str,
    *,
    processed_at: datetime | None = None,
    retry_count: int = 0,
    error: str | None = None,
    status: str | None = None,
    payload: dict[str, object] | None = None,
) -> None:
    now = datetime.now(tz=UTC)
    async with session_factory() as session:
        session.add(
            _INBOX_MODEL(
                id=event_id,
                event_type="SampleEvent",
                occurred_at=now,
                payload=payload or {},
                correlation_id="c",
                causation_id="k",
                received_at=now,
                status=status,
                processed_at=processed_at,
                retry_count=retry_count,
                error=error,
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


class TestInboxLegacyMigration:
    async def test_classifies_legacy_rows_deterministically(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        url = f"sqlite+aiosqlite:///{tmp_path / 'legacy.db'}"
        engine = create_async_engine(url)
        async with engine.begin() as connection:
            await connection.run_sync(EVENT_DELIVERY_MODELS.inbox.metadata.create_all)
        await engine.dispose()
        isolated = build_session_factory(url)

        now = datetime.now(tz=UTC)
        await _add_legacy(isolated, "legacy-pending")  # processed_at None, retry 0
        await _add_legacy(
            isolated,
            "legacy-dlq-unprocessed",
            retry_count=5,
        )  # unprocessed but retries exhausted
        await _add_legacy(
            isolated,
            "legacy-dlq-processed",
            processed_at=now,
            retry_count=5,
            error="boom",
        )
        await _add_legacy(isolated, "legacy-processed", processed_at=now)
        await _add_legacy(
            isolated,
            "legacy-exhausted",
            processed_at=None,
            retry_count=5,
            error="boom",
        )  # retries exhausted → DEAD_LETTER per plan §5.3

        migration = InboxLegacyMigration(isolated, _INBOX_MODEL, max_retries=3)
        counts = await migration.classify_legacy_rows()

        assert counts == {
            "pending": 1,
            "dead_letter": 3,
            "processed": 1,
            "legacy_review": 0,
        }

        assert (await _read_status(isolated, "legacy-pending")).status == InboxStatus.PENDING.value
        assert (
            await _read_status(isolated, "legacy-dlq-unprocessed")
        ).status == InboxStatus.DEAD_LETTER.value
        assert (
            await _read_status(isolated, "legacy-dlq-processed")
        ).status == InboxStatus.DEAD_LETTER.value
        assert (
            await _read_status(isolated, "legacy-processed")
        ).status == InboxStatus.PROCESSED.value
        assert (
            await _read_status(isolated, "legacy-exhausted")
        ).status == InboxStatus.DEAD_LETTER.value

    async def test_overwrites_stale_status_from_legacy_columns(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        """A row that already carried a default status is still classified from legacy cols."""
        url = f"sqlite+aiosqlite:///{tmp_path / 'legacy2.db'}"
        engine = create_async_engine(url)
        async with engine.begin() as connection:
            await connection.run_sync(EVENT_DELIVERY_MODELS.inbox.metadata.create_all)
        await engine.dispose()
        isolated = build_session_factory(url)

        await _add_legacy(
            isolated,
            "legacy-stale",
            processed_at=datetime.now(tz=UTC),
            retry_count=5,
            error="boom",
            status=InboxStatus.PENDING.value,  # stale default from ORM
        )

        migration = InboxLegacyMigration(isolated, _INBOX_MODEL, max_retries=3)
        counts = await migration.classify_legacy_rows()

        assert counts["dead_letter"] == 1
        assert (
            await _read_status(isolated, "legacy-stale")
        ).status == InboxStatus.DEAD_LETTER.value

    async def test_migration_preserves_payload_and_error_history(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        """Classification must never lose the payload or the error history."""
        url = f"sqlite+aiosqlite:///{tmp_path / 'legacy3.db'}"
        engine = create_async_engine(url)
        async with engine.begin() as connection:
            await connection.run_sync(EVENT_DELIVERY_MODELS.inbox.metadata.create_all)
        await engine.dispose()
        isolated = build_session_factory(url)

        payload: dict[str, object] = {"user_id": "u-1", "auth_session_id": "auth-7"}
        await _add_legacy(
            isolated,
            "legacy-payload",
            retry_count=5,
            error="boom",
            payload=payload,
        )

        migration = InboxLegacyMigration(isolated, _INBOX_MODEL, max_retries=3)
        counts = await migration.classify_legacy_rows()

        assert counts["dead_letter"] == 1
        row = await _read_status(isolated, "legacy-payload")
        assert row.status == InboxStatus.DEAD_LETTER.value
        assert row.payload == payload
        assert row.error == "boom"

    async def test_rereun_never_touches_new_processor_rows(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        """Re-running the migration (e.g. after a worker restart) is safe:
        rows already owned by the new processor are never re-classified, so
        in-flight PROCESSING and scheduled RETRY work is preserved.
        """
        url = f"sqlite+aiosqlite:///{tmp_path / 'legacy4.db'}"
        engine = create_async_engine(url)
        async with engine.begin() as connection:
            await connection.run_sync(EVENT_DELIVERY_MODELS.inbox.metadata.create_all)
        await engine.dispose()
        isolated = build_session_factory(url)

        await _add_legacy(isolated, "inflight", status=InboxStatus.PROCESSING.value)
        await _add_legacy(isolated, "scheduled", status=InboxStatus.RETRY.value)
        await _add_legacy(isolated, "done", status=InboxStatus.PROCESSED.value)
        await _add_legacy(isolated, "dead", status=InboxStatus.DEAD_LETTER.value)

        migration = InboxLegacyMigration(isolated, _INBOX_MODEL, max_retries=3)
        counts = await migration.classify_legacy_rows()

        assert counts == {
            "pending": 0,
            "dead_letter": 0,
            "processed": 0,
            "legacy_review": 0,
        }
        assert (await _read_status(isolated, "inflight")).status == InboxStatus.PROCESSING.value
        assert (await _read_status(isolated, "scheduled")).status == InboxStatus.RETRY.value
        assert (await _read_status(isolated, "done")).status == InboxStatus.PROCESSED.value
        assert (await _read_status(isolated, "dead")).status == InboxStatus.DEAD_LETTER.value

    async def test_guardrail_blocks_start_when_legacy_review_remains(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        from shell.platform.infrastructure.messaging.inbox.inbox_legacy_migration import (
            LegacyReviewBlockedError,
            assert_inbox_ready,
        )

        url = f"sqlite+aiosqlite:///{tmp_path / 'legacy5.db'}"
        engine = create_async_engine(url)
        async with engine.begin() as connection:
            await connection.run_sync(EVENT_DELIVERY_MODELS.inbox.metadata.create_all)
        await engine.dispose()
        isolated = build_session_factory(url)

        await _add_legacy(isolated, "unresolved", status=InboxStatus.LEGACY_REVIEW.value)

        with pytest.raises(LegacyReviewBlockedError):
            await assert_inbox_ready(isolated, _INBOX_MODEL)

    async def test_guardrail_passes_when_no_legacy_review(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        from shell.platform.infrastructure.messaging.inbox.inbox_legacy_migration import (
            assert_inbox_ready,
        )

        url = f"sqlite+aiosqlite:///{tmp_path / 'legacy6.db'}"
        engine = create_async_engine(url)
        async with engine.begin() as connection:
            await connection.run_sync(EVENT_DELIVERY_MODELS.inbox.metadata.create_all)
        await engine.dispose()
        isolated = build_session_factory(url)

        await _add_legacy(isolated, "ok-pending", status=InboxStatus.PENDING.value)
        count = await assert_inbox_ready(isolated, _INBOX_MODEL)
        assert count == 0
