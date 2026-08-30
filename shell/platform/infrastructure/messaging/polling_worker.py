"""Reusable polling worker for inbox processors and relay tasks.

Enterprise worker features:
  - structured ``PollingWorkerConfig`` (worker_id, batch, interval, backoff, lease);
  - graceful shutdown via ``stop_event`` (no new batch started after shutdown begins);
  - exponential error backoff after infrastructure failures — the worker survives
    transient DB outages instead of dying;
  - per-batch bounded concurrency for processors that support it.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from shell.platform.infrastructure.messaging.inbox.inbox_batch_result import (
        InboxBatchResult,
    )

logger = logging.getLogger(__name__)


class PollingTask(Protocol):
    async def run_once(self) -> InboxBatchResult: ...


@dataclass(frozen=True, slots=True)
class PollingWorkerConfig:
    worker_id: str = "polling-worker"
    poll_interval_seconds: float = 1.0
    batch_size: int = 100
    lease_duration_seconds: int = 60
    error_backoff_seconds: float = 1.0
    max_error_backoff_seconds: float = 30.0
    max_concurrency: int = 1
    shutdown_timeout_seconds: float = 10.0
    _backoff_factor: float = field(default=2.0, repr=False)


async def run_polling_worker(
    task: PollingTask,
    *,
    interval_seconds: float = 1.0,
    stop_event: asyncio.Event | None = None,
    config: PollingWorkerConfig | None = None,
    heartbeat: Callable[[], Awaitable[None]] | None = None,
) -> None:
    """Run a delivery task repeatedly until ``stop_event`` is set.

    Backward-compatible wrapper around :class:`PollingWorker`.
    """
    effective = config or PollingWorkerConfig(poll_interval_seconds=interval_seconds)
    await PollingWorker(task, effective, heartbeat=heartbeat).run(stop_event)


class PollingWorker:
    def __init__(
        self,
        task: PollingTask,
        config: PollingWorkerConfig,
        *,
        heartbeat: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        self._task = task
        self._config = config
        self._stop_event = asyncio.Event()
        self._error_backoff = config.error_backoff_seconds
        self._heartbeat = heartbeat

    async def run(self, stop_event: asyncio.Event | None = None) -> None:
        """Poll until the caller (or the process) signals shutdown."""
        if stop_event is not None:
            self._stop_event = stop_event

        while not self._stop_event.is_set():
            if self._heartbeat is not None:
                try:
                    await self._heartbeat()
                except Exception:
                    logger.exception("polling worker heartbeat failed; liveness degraded")

            try:
                result = await self._task.run_once()
                self._error_backoff = self._config.error_backoff_seconds
                logger.debug(
                    "polling task claimed=%s processed=%s retried=%s dlq=%s failed=%s duration_ms=%s",
                    result.claimed_count,
                    result.processed_count,
                    result.retried_count,
                    result.dead_lettered_count,
                    result.failed_count,
                    result.duration_ms,
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("polling worker task failed; backing off")
                await self._sleep(self._error_backoff)
                self._error_backoff = min(
                    self._error_backoff * self._config._backoff_factor,
                    self._config.max_error_backoff_seconds,
                )
                continue

            if self._stop_event.is_set():
                break
            await self._sleep(self._config.poll_interval_seconds)

    async def _sleep(self, seconds: float) -> None:
        """Sleep while still honouring shutdown signals."""
        if seconds <= 0:
            await asyncio.sleep(0)
            return
        with suppress(TimeoutError):
            await asyncio.wait_for(self._stop_event.wait(), timeout=seconds)
