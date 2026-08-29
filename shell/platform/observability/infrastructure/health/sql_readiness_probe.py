"""SqlReadinessProbe — DB-backed readiness for a bounded context inbox.

Checks, in order:

- ``database`` — a real round-trip to the DB engine;
- ``migrations`` — the platform delivery tables exist (baseline applied);
- ``worker`` — at least one inbox record is currently held under a fresh lease
  (a worker is processing) or there is nothing to process;
- ``backlog`` — the pending+retry backlog stays under ``max_backlog``.

The report is ready only when every check passes. Any check that fails (DB
down, backlog flooded) reports the failure instead of raising, so the endpoint
can answer 503 with a diagnostic body.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Protocol

from sqlalchemy import func, select, text

from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.observability.application.ports.readiness import (
    ReadinessProbe,
    ReadinessReport,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from sqlalchemy.orm import Mapped

    from shell.platform.infrastructure.messaging.inbox.inbox_claim_service import (
        InboxStateModel,
    )


class _WorkerHeartbeatReadModel(Protocol):
    """Read shape of the worker heartbeat model used by the probe."""

    last_seen_at: Mapped[datetime]


class SqlReadinessProbe(ReadinessProbe):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        inbox_model: type[InboxStateModel],
        max_backlog: int = 1000,
        worker_heartbeat_model: type[_WorkerHeartbeatReadModel] | None = None,
        worker_stale_after_seconds: float = 30.0,
    ) -> None:
        self._session_factory = session_factory
        self._inbox_model = inbox_model
        self._max_backlog = max_backlog
        self._worker_heartbeat_model = worker_heartbeat_model
        self._worker_stale_after_seconds = worker_stale_after_seconds

    async def check(self) -> ReadinessReport:
        checks: dict[str, object] = {}
        try:
            async with self._session_factory() as session:
                checks["database"] = await self._check_database(session)
                checks["migrations"] = await self._check_migrations(session)
                checks["worker"] = await self._check_worker(session)
                checks["backlog"] = await self._check_backlog(session)
        except Exception as exc:  # noqa: BLE001 — readiness must never raise
            checks["database"] = f"error: {type(exc).__name__}: {exc}"
            checks["migrations"] = "not checked"
            checks["worker"] = "not checked"
            checks["backlog"] = "not checked"

        ready = all(isinstance(value, bool) and value is True for value in checks.values())
        return ReadinessReport(ready=ready, checks=checks)

    async def _check_database(self, session: AsyncSession) -> bool:
        await session.execute(text("SELECT 1"))
        return True

    async def _check_migrations(self, session: AsyncSession) -> bool:
        """Probe the delivery table — it exists only after the baseline ran."""
        try:
            await session.execute(select(func.count()).select_from(self._inbox_model))
            return True
        except Exception:
            return False

    async def _check_worker(self, session: AsyncSession) -> bool:
        """A worker is alive when it recorded a fresh heartbeat.

        Falls back to lease holders when no heartbeat table is configured. A
        configured heartbeat table is authoritative: no fresh heartbeat is not
        ready even when the inbox is currently empty.
        """
        if self._worker_heartbeat_model is not None:
            now = await self._database_now(session)
            fresh = await session.execute(
                select(func.count())
                .select_from(self._worker_heartbeat_model)
                .where(
                    self._worker_heartbeat_model.last_seen_at
                    > now - timedelta(seconds=self._worker_stale_after_seconds)
                )
            )
            return fresh.scalar_one() > 0
        else:
            now = await self._database_now(session)
            active_holders = (
                await session.execute(
                    select(func.count())
                    .select_from(self._inbox_model)
                    .where(
                        self._inbox_model.status == InboxStatus.PROCESSING.value,
                        self._inbox_model.lease_until > now,
                    )
                )
            ).scalar_one()
            if active_holders > 0:
                return True

        backlog = await session.execute(
            select(func.count())
            .select_from(self._inbox_model)
            .where(
                self._inbox_model.status.in_([InboxStatus.PENDING.value, InboxStatus.RETRY.value])
            )
        )
        return backlog.scalar_one() == 0

    async def _check_backlog(self, session: AsyncSession) -> bool:
        result = await session.execute(
            select(func.count())
            .select_from(self._inbox_model)
            .where(
                self._inbox_model.status.in_([InboxStatus.PENDING.value, InboxStatus.RETRY.value])
            )
        )
        backlog = result.scalar_one()
        return backlog <= self._max_backlog

    async def _database_now(self, session: AsyncSession) -> datetime:
        raw = (await session.execute(select(func.current_timestamp()))).scalar_one()
        if isinstance(raw, str):
            raw = datetime.fromisoformat(raw)
        if raw.tzinfo is None:
            raw = raw.replace(tzinfo=UTC)
        return raw
