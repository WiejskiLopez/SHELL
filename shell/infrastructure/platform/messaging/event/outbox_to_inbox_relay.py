"""OutboxToInboxRelay — reads pending outbox_event rows and re-publishes to an EventPublisher.

Intended as a one-shot or periodic background task:
    relay = OutboxToInboxRelay(session_factory, downstream_publisher)
    await relay.run_once()   # processes all pending rows in one pass

Concurrency safety: uses SELECT FOR UPDATE SKIP LOCKED on dialects that support
it (PostgreSQL).  On SQLite (single-writer) the clause is omitted automatically.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from shell.infrastructure.platform.persistence.sql.models import InboxEventModel, OutboxEventModel

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.application.platform.ports.ports import EventPublisher

logger = logging.getLogger(__name__)


class OutboxToInboxRelay:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        downstream: EventPublisher | None = None,
        batch_size: int = 100,
    ) -> None:
        self._session_factory = session_factory
        self._downstream = downstream
        self._batch_size = batch_size

        engine = getattr(session_factory, "bind", None)
        dialect_name: str = engine.dialect.name if engine is not None else "unknown"
        self._skip_locked: bool = dialect_name not in ("sqlite",)
        self._is_postgres: bool = dialect_name == "postgresql"

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

            if self._is_postgres:
                await self._batch_insert_postgres(session, rows, now)
            else:
                await self._batch_insert_sqlite(session, rows, now)

            await session.commit()
            return len(rows)

    async def _batch_insert_postgres(
        self,
        session: AsyncSession,
        rows: Sequence[OutboxEventModel],
        now: datetime,
    ) -> None:
        values = [
            {
                "id": row.id,
                "event_type": row.event_type,
                "occurred_at": row.occurred_at,
                "payload": row.payload,
                "correlation_id": row.correlation_id,
                "causation_id": row.causation_id,
                "received_at": now,
                "processed_at": None,
            }
            for row in rows
        ]
        insert_stmt = pg_insert(InboxEventModel).values(values)
        upsert_stmt = insert_stmt.on_conflict_do_nothing(index_elements=["id"])
        await session.execute(upsert_stmt)

        for row in rows:
            row.published_at = now

    async def _batch_insert_sqlite(
        self,
        session: AsyncSession,
        rows: Sequence[OutboxEventModel],
        now: datetime,
    ) -> None:
        import sqlalchemy as sa

        values = [
            {
                "id": row.id,
                "event_type": row.event_type,
                "occurred_at": row.occurred_at,
                "payload": row.payload,
                "correlation_id": row.correlation_id,
                "causation_id": row.causation_id,
                "received_at": now,
                "processed_at": None,
            }
            for row in rows
        ]
        stmt = sa.insert(InboxEventModel).values(values)
        stmt = stmt.prefix_with("OR IGNORE")
        await session.execute(stmt)

        for row in rows:
            row.published_at = now
