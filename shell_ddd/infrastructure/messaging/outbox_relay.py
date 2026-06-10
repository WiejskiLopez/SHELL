"""OutboxRelay — reads pending outbox_event rows and re-publishes to an EventPublisher.

Intended as a one-shot or periodic background task:
    relay = OutboxRelay(session_factory, downstream_publisher)
    await relay.run_once()   # processes all pending rows in one pass

Concurrency safety: uses SELECT FOR UPDATE SKIP LOCKED on dialects that support
it (PostgreSQL).  On SQLite (single-writer) the clause is omitted automatically.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select, update

from shell_ddd.infrastructure.persistence.sql.models import OutboxEventModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell_ddd.application.ports.ports import EventPublisher


class OutboxRelay:
    """Reads unpublished outbox rows and forwards them to the downstream publisher."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        downstream: EventPublisher,
        batch_size: int = 100,
    ) -> None:
        self._session_factory = session_factory
        self._downstream = downstream
        self._batch_size = batch_size
        # Detect once at construction time whether the DB supports SKIP LOCKED.
        # SQLite does not support FOR UPDATE; PostgreSQL does.
        engine = getattr(session_factory, "bind", None)
        dialect_name: str = engine.dialect.name if engine is not None else "unknown"
        self._skip_locked: bool = dialect_name not in ("sqlite",)

    async def run_once(self) -> int:
        """Process one batch of pending outbox events.

        Returns the number of events processed.
        """
        async with self._session_factory() as session:
            stmt = (
                select(OutboxEventModel)
                .where(OutboxEventModel.published_at.is_(None))
                .order_by(OutboxEventModel.occurred_at)
                .limit(self._batch_size)
            )
            if self._skip_locked:
                # Prevents two relay workers from picking the same rows.
                # Row-level lock is released after the UPDATE below commits.
                stmt = stmt.with_for_update(skip_locked=True)

            rows = (await session.execute(stmt)).scalars().all()

            if not rows:
                return 0

            # Build lightweight event wrappers for the downstream publisher
            events: list[_OutboxProxy] = [_OutboxProxy(r) for r in rows]
            await self._downstream.publish(events)  # type: ignore[arg-type]

            now = datetime.now(tz=UTC)
            ids = [r.id for r in rows]
            await session.execute(
                update(OutboxEventModel)
                .where(OutboxEventModel.id.in_(ids))
                .values(published_at=now)
            )
            await session.commit()
            return len(rows)


class _OutboxProxy:
    """Thin wrapper exposing the minimal interface expected by EventPublisher.publish().

    The downstream publisher only needs ``type(event).__name__`` and
    ``event.occurred_at``; everything else lives in ``payload``.
    """

    def __init__(self, row: OutboxEventModel) -> None:
        self._row = row
        self.occurred_at: datetime = row.occurred_at
        self.event_type: str = row.event_type
        self.payload: dict = row.payload  # type: ignore[type-arg]

    def __class_getitem__(cls, item: object) -> object:  # pragma: no cover
        return cls
