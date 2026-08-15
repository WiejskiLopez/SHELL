"""InboxLegacyMigration — one-shot deterministic classification of legacy inbox rows.

Applies the plan's classification rule to inboxes that predate the explicit
status column. The operator runs it once **before** switching on the new
processor; it classifies every existing row deterministically from the legacy
columns:

  - ``processed_at IS NULL`` (retry not exhausted)       → ``PENDING``
  - ``processed_at IS NULL`` and retry exhausted         → ``DEAD_LETTER``
  - ``processed_at IS NOT NULL`` and retry exhausted
    and error recorded                                   → ``DEAD_LETTER``
  - ``processed_at IS NOT NULL`` (otherwise)             → ``PROCESSED``
  - anything that violates the above assumptions         → ``LEGACY_REVIEW``

The migration is forward-only: existing payloads are never modified, and every
row ends in a deterministic, operator-resolvable state. New rows written after
the migration are untouched by later runs because they already carry an explicit
status — re-running the migration is a no-op for them only if run before the
processor is active.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, cast

from sqlalchemy import func, or_, select, update

from shell.platform.domain.value_objects.inbox_status import InboxStatus

if TYPE_CHECKING:
    from sqlalchemy.engine import CursorResult
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from sqlalchemy.sql.elements import ColumnElement

    from shell.platform.infrastructure.messaging.inbox.inbox_claim_service import (
        InboxStateModel,
    )

logger = logging.getLogger(__name__)

_DEFAULT_MAX_RETRIES = 3


class LegacyReviewBlockedError(RuntimeError):
    """Raised when unclassified legacy inbox rows remain before worker start."""


async def assert_inbox_ready(
    session_factory: async_sessionmaker[AsyncSession],
    inbox_model: type[InboxStateModel],
) -> int:
    """Guardrail: fail fast when any ``LEGACY_REVIEW`` row remains.

    Runs read-only before starting a worker/processor. A nonzero count means the
    operator must run the legacy data migration (``--run-legacy-migration``) once
    before enabling the new processor (ref2.md §3.1.D).
    """
    async with session_factory() as session:
        count = int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(inbox_model)
                    .where(inbox_model.status == InboxStatus.LEGACY_REVIEW.value)
                )
            ).scalar_one()
        )
    if count > 0:
        raise LegacyReviewBlockedError(
            f"LEGACY_REVIEW rows remain: {count}. Run the legacy inbox migration before "
            "starting the worker."
        )
    return count


class InboxLegacyMigration:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        inbox_model: type[InboxStateModel],
        max_retries: int = _DEFAULT_MAX_RETRIES,
    ) -> None:
        self._session_factory = session_factory
        self._inbox_model = inbox_model
        self._max_retries = max_retries

    async def classify_legacy_rows(self) -> dict[str, int]:
        """Classify every existing legacy inbox row from its legacy columns.

        Only rows that still carry the legacy status (``NULL`` or ``PENDING``
        default) are classified — rows already owned by the new processor
        (``PROCESSING`` / ``RETRY`` / ``DEAD_LETTER`` / ``PROCESSED``) are never
        touched, so re-running the migration while a worker is active cannot
        corrupt in-flight work.
        """
        async with self._session_factory() as session:
            legacy = self._legacy_status_filter()
            pending_ids = await self._ids_with(
                session,
                legacy,
                self._inbox_model.processed_at.is_(None),
                self._inbox_model.retry_count < self._max_retries,
            )
            dlq_unprocessed = await self._ids_with(
                session,
                legacy,
                self._inbox_model.processed_at.is_(None),
                self._inbox_model.retry_count >= self._max_retries,
            )
            dlq_processed = await self._ids_with(
                session,
                legacy,
                self._inbox_model.processed_at.is_not(None),
                self._inbox_model.retry_count >= self._max_retries,
                self._inbox_model.error.is_not(None),
            )
            processed = await self._ids_with(
                session,
                legacy,
                self._inbox_model.processed_at.is_not(None),
                (self._inbox_model.retry_count >= self._max_retries)
                .__and__(self._inbox_model.error.is_not(None))
                .__invert__(),
            )
            all_ids = await self._ids_with(session, legacy)
            legacy_review = all_ids - pending_ids - dlq_unprocessed - dlq_processed - processed

            now = datetime.now(tz=UTC)
            counts = {"pending": 0, "dead_letter": 0, "processed": 0, "legacy_review": 0}

            counts["pending"] = await self._mark(
                session, pending_ids, InboxStatus.PENDING.value, now, reset_error=True
            )
            counts["dead_letter"] = await self._mark(
                session, dlq_unprocessed, InboxStatus.DEAD_LETTER.value, now, failed=True
            )
            counts["dead_letter"] += await self._mark(
                session, dlq_processed, InboxStatus.DEAD_LETTER.value, now, failed=True
            )
            counts["processed"] = await self._mark(
                session, processed, InboxStatus.PROCESSED.value, now
            )
            counts["legacy_review"] = await self._mark(
                session, legacy_review, InboxStatus.LEGACY_REVIEW.value, now
            )

            await session.commit()

        logger.info("inbox.legacy_migration counts=%s", counts)
        return counts

    async def _ids_with(self, session: AsyncSession, *conditions: ColumnElement[bool]) -> set[str]:
        rows = (await session.execute(select(self._inbox_model.id).where(*conditions))).scalars()
        return set(rows)

    def _legacy_status_filter(self) -> ColumnElement[bool]:
        """Rows not yet owned by the new processor (legacy status only)."""
        return or_(
            self._inbox_model.status.is_(None),
            self._inbox_model.status == InboxStatus.PENDING.value,
        )

    async def _mark(
        self,
        session: AsyncSession,
        ids: set[str],
        status: str,
        now: datetime,
        *,
        reset_error: bool = False,
        failed: bool = False,
    ) -> int:
        if not ids:
            return 0
        values: dict[str, object] = {"status": status}
        if reset_error:
            values["error"] = None
        if failed:
            values["failed_at"] = now
        if status == InboxStatus.PENDING.value:
            values["next_attempt_at"] = now
        if status == InboxStatus.DEAD_LETTER.value:
            values["next_attempt_at"] = now + timedelta(days=365 * 10)
        result = await session.execute(
            update(self._inbox_model).where(self._inbox_model.id.in_(ids)).values(**values)
        )
        return int(cast("CursorResult[object]", result).rowcount or 0)
