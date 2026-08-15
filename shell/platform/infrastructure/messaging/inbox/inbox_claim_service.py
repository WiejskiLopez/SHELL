"""InboxClaimService — atomically claims inbox delivery records with a lease.

Replaces the long database lock of the legacy processor with a short claim
transaction: a worker selects pending/retry records, marks them ``PROCESSING``,
sets ``claimed_by`` and a ``lease_until``, and commits. Records left behind by a
dead worker are reclaimed once their lease expires.

All timing uses the database clock (``CURRENT_TIMESTAMP``) so lease expiry is
consistent across workers regardless of app-machine clock drift.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Protocol, cast

from sqlalchemy import and_, func, or_, select

from shell.platform.domain.value_objects.inbox_status import InboxStatus

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from sqlalchemy.orm import Mapped


class InboxStateModel(Protocol):
    """Columns a claimable inbox model must expose (provided by ``InboxStateMixin``)."""

    id: Mapped[str]
    status: Mapped[str]
    next_attempt_at: Mapped[datetime]
    lease_until: Mapped[datetime | None]
    claimed_by: Mapped[str | None]
    received_at: Mapped[datetime]
    processed_at: Mapped[datetime | None]
    failed_at: Mapped[datetime | None]
    last_attempted_at: Mapped[datetime | None]
    retry_count: Mapped[int]
    error: Mapped[str | None]
    error_code: Mapped[str | None]
    error_message: Mapped[str | None]
    schema_version: Mapped[int]


class _ClaimableRow(Protocol):
    """Runtime instance shape used while mutating claimed rows."""

    status: str
    lease_until: datetime | None
    claimed_by: str | None


class InboxClaimService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        inbox_model: type[InboxStateModel],
        worker_id: str,
        lease_duration_seconds: int,
        batch_size: int = 100,
    ) -> None:
        self._session_factory = session_factory
        self._inbox_model = inbox_model
        self._worker_id = worker_id
        self._lease_duration_seconds = lease_duration_seconds
        self._batch_size = batch_size

        engine = getattr(session_factory, "bind", None)
        dialect_name: str = engine.dialect.name if engine is not None else "unknown"
        self._skip_locked: bool = dialect_name not in ("sqlite",)

    async def claim_batch(self, limit: int | None = None) -> list[object]:
        """Claim up to ``batch_size`` records in a single short transaction.

        ``limit`` overrides the configured batch size for this call (used by the
        processor to force a single-element batch when heartbeat is disabled).

        Returns the claimed records (status ``PROCESSING``, ``claimed_by`` and
        ``lease_until`` already written and committed). Callers own the result
        rows and are expected to process them and acknowledge afterwards.
        """
        batch_size = limit if limit is not None else self._batch_size
        async with self._session_factory() as session:
            now = await self._database_now(session)

            stmt = (
                select(self._inbox_model)
                .where(
                    or_(
                        and_(
                            self._inbox_model.status.in_(
                                [InboxStatus.PENDING.value, InboxStatus.RETRY.value]
                            ),
                            self._inbox_model.next_attempt_at <= now,
                        ),
                        and_(
                            self._inbox_model.status == InboxStatus.PROCESSING.value,
                            self._inbox_model.lease_until < now,
                        ),
                    )
                )
                .order_by(self._inbox_model.received_at)
                .limit(batch_size)
            )
            if self._skip_locked:
                stmt = stmt.with_for_update(skip_locked=True)

            rows = (await session.execute(stmt)).scalars().all()

            claimed: list[object] = []
            for row in rows:
                mutable = cast("_ClaimableRow", row)
                mutable.status = InboxStatus.PROCESSING.value
                mutable.claimed_by = self._worker_id
                mutable.lease_until = now + timedelta(seconds=self._lease_duration_seconds)
                claimed.append(row)

            await session.commit()
            return claimed

    async def _database_now(self, session: AsyncSession) -> datetime:
        raw = (await session.execute(select(func.current_timestamp()))).scalar_one()
        if isinstance(raw, str):
            raw = datetime.fromisoformat(raw)
        if raw.tzinfo is None:
            raw = raw.replace(tzinfo=UTC)
        return raw
