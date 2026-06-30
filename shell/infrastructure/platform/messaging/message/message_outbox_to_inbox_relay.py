"""MessageOutboxToInboxRelay — reads pending outbox_message rows and inserts into inbox_message."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from shell.infrastructure.platform.persistence.sql.models.message.inbox_message import (
    InboxMessageModel,
)
from shell.infrastructure.platform.persistence.sql.models.message.outbox_message import (
    OutboxMessageModel,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


class MessageOutboxToInboxRelay:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        batch_size: int = 100,
    ) -> None:
        self._session_factory = session_factory
        self._batch_size = batch_size

        engine = getattr(session_factory, "bind", None)
        dialect_name: str = engine.dialect.name if engine is not None else "unknown"
        self._skip_locked: bool = dialect_name not in ("sqlite",)
        self._is_postgres: bool = dialect_name == "postgresql"

    async def run_once(self) -> int:
        async with self._session_factory() as session:
            stmt = (
                select(OutboxMessageModel)
                .where(OutboxMessageModel.published_at.is_(None))
                .order_by(OutboxMessageModel.created_at)
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
        rows: Sequence[OutboxMessageModel],
        now: datetime,
    ) -> None:
        values = [
            {
                "id": row.id,
                "envelope": row.envelope,
                "created_at": row.created_at,
                "received_at": now,
                "processed_at": None,
                "error": None,
            }
            for row in rows
        ]
        insert_stmt = pg_insert(InboxMessageModel).values(values)
        upsert_stmt = insert_stmt.on_conflict_do_nothing(index_elements=["id"])
        await session.execute(upsert_stmt)

        for row in rows:
            row.published_at = now

    async def _batch_insert_sqlite(
        self,
        session: AsyncSession,
        rows: Sequence[OutboxMessageModel],
        now: datetime,
    ) -> None:
        import sqlalchemy as sa

        values = [
            {
                "id": row.id,
                "envelope": row.envelope,
                "created_at": row.created_at,
                "received_at": now,
                "processed_at": None,
                "error": None,
            }
            for row in rows
        ]
        stmt = sa.insert(InboxMessageModel).values(values)
        stmt = stmt.prefix_with("OR IGNORE")
        await session.execute(stmt)

        for row in rows:
            row.published_at = now
