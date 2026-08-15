"""WorkerHeartbeatRecorder — records a worker's liveness for readiness probes.

A polling worker writes ``worker_id`` + ``last_seen_at`` into the per-BC
``worker_heartbeat`` table on every poll iteration. Readiness probes can then
answer "is a worker actually alive?" from fresh heartbeats instead of inferring
liveness from lease holders (ref4.md Krok 4).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class WorkerHeartbeatRecorder:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        model: type[Any],
        worker_id: str,
    ) -> None:
        self._session_factory = session_factory
        self._model = model
        self._worker_id = worker_id

    async def beat(self) -> None:
        """Upsert ``last_seen_at`` for this worker (one row per worker_id)."""
        async with self._session_factory() as session:
            database_now = (await session.execute(select(func.current_timestamp()))).scalar_one()
            await session.merge(
                self._model(
                    worker_id=self._worker_id,
                    last_seen_at=database_now,
                )
            )
            await session.commit()
