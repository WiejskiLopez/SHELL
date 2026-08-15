"""MessageOutboxToInboxRelay — reads pending outbox_message rows and forwards to a MessagePublisher.

Intended as a one-shot or periodic background task:
    relay = MessageOutboxToInboxRelay(session_factory, downstream_publisher)
    await relay.run_once()   # processes all pending rows in one pass

Concurrency safety: uses SELECT FOR UPDATE SKIP LOCKED on dialects that support
it (PostgreSQL).  On SQLite (single-writer) the clause is omitted automatically.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol, cast

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from sqlalchemy.orm import Mapped

    from shell.platform.application.ports.messaging import MessagePublisher
    from shell.platform.infrastructure.persistence.sql.models.message_delivery import (
        MessageDeliveryModels,
    )

logger = logging.getLogger(__name__)


class MessageOutboxModel(Protocol):
    """Outbox_message columns used for the pending-row SELECT (class-level access)."""

    id: Mapped[str]
    message_type: Mapped[str]
    occurred_at: Mapped[datetime]
    payload: Mapped[dict[str, object]]
    correlation_id: Mapped[str]
    causation_id: Mapped[str]
    published_at: Mapped[datetime | None]


class MessageOutboxRow(Protocol):
    """Runtime instance shape of a pending outbox_message row."""

    id: str
    message_type: str
    occurred_at: datetime
    payload: dict[str, object]
    correlation_id: str
    causation_id: str
    published_at: datetime | None


class MessageOutboxToInboxRelay:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        downstream: MessagePublisher | None = None,
        batch_size: int = 100,
        *,
        models: MessageDeliveryModels,
        target_session_factory: async_sessionmaker[AsyncSession] | None = None,
        target_models: MessageDeliveryModels | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._downstream = downstream
        self._batch_size = batch_size
        self._inbox_model = models.inbox
        self._outbox_model = cast("type[MessageOutboxModel]", models.outbox)
        self._target_session_factory = target_session_factory or session_factory
        self._target_inbox_model = (
            target_models.inbox if target_models is not None else self._inbox_model
        )

        engine = getattr(session_factory, "bind", None)
        dialect_name: str = engine.dialect.name if engine is not None else "unknown"
        self._skip_locked: bool = dialect_name not in ("sqlite",)
        self._is_postgres: bool = dialect_name == "postgresql"

    async def run_once(self) -> int:
        async with self._session_factory() as session:
            stmt = (
                select(self._outbox_model)
                .where(self._outbox_model.published_at.is_(None))
                .order_by(self._outbox_model.occurred_at)
                .limit(self._batch_size)
            )
            if self._skip_locked:
                stmt = stmt.with_for_update(skip_locked=True)

            rows = (await session.execute(stmt)).scalars().all()
            if not rows:
                return 0

            now = datetime.now(tz=UTC)

            async with self._target_session_factory() as target_session:
                if self._is_postgres:
                    await self._batch_insert_postgres(target_session, rows, now)
                else:
                    await self._batch_insert_sqlite(target_session, rows, now)
                await target_session.commit()

            await session.commit()
            return len(rows)

    async def _batch_insert_postgres(
        self,
        session: AsyncSession,
        rows: Sequence[object],
        now: datetime,
    ) -> None:
        typed_rows = cast("Sequence[MessageOutboxRow]", rows)
        values = [
            {
                "id": row.id,
                "message_type": row.message_type,
                "occurred_at": row.occurred_at,
                "payload": row.payload,
                "correlation_id": row.correlation_id,
                "causation_id": row.causation_id,
                "received_at": now,
                "processed_at": None,
            }
            for row in typed_rows
        ]
        insert_stmt = pg_insert(self._target_inbox_model).values(values)
        upsert_stmt = insert_stmt.on_conflict_do_nothing(index_elements=["id"])
        await session.execute(upsert_stmt)

        for row in typed_rows:
            row.published_at = now

    async def _batch_insert_sqlite(
        self,
        session: AsyncSession,
        rows: Sequence[object],
        now: datetime,
    ) -> None:
        typed_rows = cast("Sequence[MessageOutboxRow]", rows)
        values = [
            {
                "id": row.id,
                "message_type": row.message_type,
                "occurred_at": row.occurred_at,
                "payload": row.payload,
                "correlation_id": row.correlation_id,
                "causation_id": row.causation_id,
                "received_at": now,
                "processed_at": None,
            }
            for row in typed_rows
        ]
        stmt = sa.insert(self._target_inbox_model).values(values)
        stmt = stmt.prefix_with("OR IGNORE")
        await session.execute(stmt)

        for row in typed_rows:
            row.published_at = now
