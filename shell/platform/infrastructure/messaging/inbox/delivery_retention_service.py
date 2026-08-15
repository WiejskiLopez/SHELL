"""DeliveryRetentionService — bounded retention/cleanup for delivery tables.

Policies (ref2.md §5 Faza 5, ref2.md §7):

- DLQ inbox rows older than ``dead_letter_retention_days`` are purged — the
  payload, type and error metadata are no longer operationally actionable;
- ``processed_delivery`` dedup rows older than ``processed_delivery_retention_days``
  are purged — the replay window has closed and the dedup guard is no longer
  needed.

Retention windows are configurable. Purges run in a single transaction per
table so a crash leaves the tables consistent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Protocol, cast

from sqlalchemy import delete, func, select

from shell.platform.domain.value_objects.inbox_status import InboxStatus

if TYPE_CHECKING:
    from sqlalchemy.engine import CursorResult
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from sqlalchemy.orm import Mapped
    from sqlalchemy.sql.dml import Delete
    from sqlalchemy.sql.elements import ColumnElement

    from shell.platform.infrastructure.messaging.inbox.inbox_claim_service import (
        InboxStateModel,
    )


class _ProcessedDeliveryModel(Protocol):
    """Columns the dedup model must expose for retention."""

    processed_at: Mapped[datetime]


@dataclass(frozen=True, slots=True)
class RetentionReport:
    purged_dead_letter: int = 0
    purged_processed_delivery: int = 0
    kept_dead_letter: int = 0
    kept_processed_delivery: int = 0
    detail: dict[str, object] = field(default_factory=dict)


class DeliveryRetentionService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        inbox_model: type[InboxStateModel],
        processed_delivery_model: type[_ProcessedDeliveryModel],
        *,
        dead_letter_retention_days: int = 90,
        processed_delivery_retention_days: int = 30,
        now: datetime | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._inbox_model = inbox_model
        self._processed_delivery_model = processed_delivery_model
        self._dead_letter_cutoff = (now or datetime.now(tz=UTC)) - timedelta(
            days=dead_letter_retention_days
        )
        self._dedup_cutoff = (now or datetime.now(tz=UTC)) - timedelta(
            days=processed_delivery_retention_days
        )

    async def purge_expired(self) -> RetentionReport:
        async with self._session_factory() as session:
            kept_dead_letter = await self._count(
                session,
                self._inbox_model.status == InboxStatus.DEAD_LETTER.value,
            )
            purged_dead_letter = await self._delete(
                session,
                delete(self._inbox_model).where(
                    self._inbox_model.status == InboxStatus.DEAD_LETTER.value,
                    self._inbox_model.failed_at < self._dead_letter_cutoff,
                ),
            )

            dedup_model = cast("type[InboxStateModel]", self._processed_delivery_model)
            kept_processed_delivery = await self._count(
                session,
                dedup_model.processed_at.is_not(None),
                model=dedup_model,
            )
            purged_processed_delivery = await self._delete(
                session,
                delete(dedup_model).where(dedup_model.processed_at < self._dedup_cutoff),
            )

            await session.commit()

        return RetentionReport(
            purged_dead_letter=purged_dead_letter,
            purged_processed_delivery=purged_processed_delivery,
            kept_dead_letter=kept_dead_letter,
            kept_processed_delivery=kept_processed_delivery,
            detail={
                "dead_letter_cutoff": self._dead_letter_cutoff.isoformat(),
                "processed_delivery_cutoff": self._dedup_cutoff.isoformat(),
            },
        )

    async def _count(
        self,
        session: AsyncSession,
        condition: ColumnElement[bool],
        *,
        model: type[InboxStateModel] | None = None,
    ) -> int:
        target = model or self._inbox_model
        result = await session.execute(select(func.count()).select_from(target).where(condition))
        return int(result.scalar_one())

    async def _delete(self, session: AsyncSession, statement: Delete) -> int:
        result = await session.execute(statement)
        return int(cast("CursorResult[object]", result).rowcount or 0)
