"""InboxReplayService — safe administrative replay of inbox delivery records.

Replay resets a delivery back to ``PENDING`` so a worker picks it up again. The
reset is **exclusive vs active workers**: a record currently ``PROCESSING`` with
an unexpired lease is never touched, so replay cannot race a live worker.

Replay preserves the original payload and error history semantics — it clears the
operational lifecycle fields (status/retry/error/lease) but never the payload,
type or correlation/causation ids. Every replay is recorded with the operator and
reason for auditability.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
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


class InboxReplayService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        inbox_model: type[InboxStateModel],
    ) -> None:
        self._session_factory = session_factory
        self._inbox_model = inbox_model

    async def replay_by_id(
        self,
        record_id: str,
        *,
        operator: str,
        reason: str,
    ) -> bool:
        """Reset a single delivery to ``PENDING``.

        Returns ``True`` when the record was replayed. A record actively held by
        a worker (``PROCESSING`` with unexpired lease) is skipped.
        """
        async with self._session_factory() as session:
            now = await self._database_now(session)
            result = await session.execute(
                update(self._inbox_model)
                .where(
                    self._inbox_model.id == record_id,
                    self._is_replayable(self._inbox_model),
                )
                .values(**self._reset_values(now))
            )
            await session.commit()

        replayed = cast("CursorResult[object]", result).rowcount > 0
        if replayed:
            logger.info(
                "inbox.replay id=%s operator=%s reason=%s",
                record_id,
                operator,
                reason,
            )
        return replayed

    async def replay_processed(self, *, operator: str, reason: str) -> int:
        """Reset every ``PROCESSED`` record back to ``PENDING``.

        Returns the number of records replayed.
        """
        return await self._replay_many(
            status_filter=InboxStatus.PROCESSED.value,
            operator=operator,
            reason=reason,
        )

    async def replay_dead_lettered(self, *, operator: str, reason: str) -> int:
        """Reset every ``DEAD_LETTER`` record back to ``PENDING``.

        Returns the number of records replayed.
        """
        return await self._replay_many(
            status_filter=InboxStatus.DEAD_LETTER.value,
            operator=operator,
            reason=reason,
        )

    async def _replay_many(
        self,
        *,
        status_filter: str,
        operator: str,
        reason: str,
    ) -> int:
        async with self._session_factory() as session:
            now = await self._database_now(session)
            stmt = (
                update(self._inbox_model)
                .where(
                    self._inbox_model.status == status_filter,
                    self._is_replayable(self._inbox_model),
                )
                .values(**self._reset_values(now))
            )
            result = await session.execute(stmt)
            await session.commit()

        count = cast("CursorResult[object]", result).rowcount
        logger.info(
            "inbox.replay batch status=%s count=%s operator=%s reason=%s",
            status_filter,
            count,
            operator,
            reason,
        )
        return count

    def _is_replayable(self, model: type[InboxStateModel]) -> ColumnElement[bool]:
        return or_(
            model.status != InboxStatus.PROCESSING.value,
            model.lease_until < func.current_timestamp(),
        )

    def _reset_values(self, now: datetime) -> dict[str, object]:
        return {
            "status": InboxStatus.PENDING.value,
            "next_attempt_at": now,
            "retry_count": 0,
            "last_attempted_at": None,
            "lease_until": None,
            "claimed_by": None,
            "processed_at": None,
            "failed_at": None,
            "error_code": None,
            "error_message": None,
        }

    async def _database_now(self, session: AsyncSession) -> datetime:
        raw = (await session.execute(select(func.current_timestamp()))).scalar_one()
        if isinstance(raw, str):
            raw = datetime.fromisoformat(raw)
        if raw.tzinfo is None:
            raw = raw.replace(tzinfo=UTC)
        return raw
