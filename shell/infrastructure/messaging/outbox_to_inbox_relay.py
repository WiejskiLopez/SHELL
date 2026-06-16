"""OutboxToInboxRelay — reads pending outbox_event rows and re-publishes to an EventPublisher.

Intended as a one-shot or periodic background task:
    relay = OutboxToInboxRelay(session_factory, downstream_publisher)
    await relay.run_once()   # processes all pending rows in one pass

Concurrency safety: uses SELECT FOR UPDATE SKIP LOCKED on dialects that support
it (PostgreSQL).  On SQLite (single-writer) the clause is omitted automatically.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.infrastructure.persistence.sql.models import InboxEventModel, OutboxEventModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.application.ports.ports import EventPublisher


class OutboxToInboxRelay:
    def __init__(
            self,
            session_factory: async_sessionmaker[AsyncSession],
            downstream: EventPublisher | None = None, # publisher zostaje bo potem bedziemy to wyrzucac na kolejke
            batch_size: int = 100,
    ) -> None:
        self._session_factory = session_factory
        self._downstream = downstream  # zostawiamy bo potem to bedzie szlo na kolejke
        self._batch_size = batch_size

        engine = getattr(session_factory, "bind", None)
        dialect_name: str = engine.dialect.name if engine is not None else "unknown"
        self._skip_locked: bool = dialect_name not in ("sqlite",)

    async def run_once(self) -> int:
        async with self._session_factory() as session:
            stmt = (
                select(OutboxEventModel)
                .where(OutboxEventModel.published_at.is_(None))
                .order_by(OutboxEventModel.occurred_at)
                .limit(self._batch_size)
            )
            if self._skip_locked:
                stmt = stmt.with_for_update(skip_locked=True)

            rows = (await session.execute(stmt)).scalars().all()
            if not rows:
                return 0

            now = datetime.now(tz=UTC)

            # In one transaction: mark Outbox as sent AND write to Inbox!
            for r in rows:
                inbox_event = InboxEventModel(
                    id=r.id,
                    event_type=r.event_type,
                    occurred_at=r.occurred_at,
                    payload=r.payload,
                    received_at=now,
                    processed_at=None
                )
                await session.merge(inbox_event)  # merge protects against duplicate key

                r.published_at = now

            await session.commit()
            return len(rows)