"""Unit tests for the platform polling worker."""

from __future__ import annotations

import asyncio

from shell.platform.infrastructure.messaging.inbox.inbox_batch_result import InboxBatchResult
from shell.platform.infrastructure.messaging.polling_worker import (
    PollingWorker,
    PollingWorkerConfig,
    run_polling_worker,
)


def _result(claimed: int = 1) -> InboxBatchResult:
    return InboxBatchResult(
        claimed_count=claimed,
        processed_count=claimed,
        retried_count=0,
        dead_lettered_count=0,
        failed_count=0,
        duration_ms=1,
    )


class StoppingTask:
    def __init__(self, stop_event: asyncio.Event) -> None:
        self.calls = 0
        self._stop_event = stop_event

    async def run_once(self) -> InboxBatchResult:
        self.calls += 1
        self._stop_event.set()
        return _result()


class FailingTask:
    def __init__(self, stop_event: asyncio.Event, *, failures: int = 1) -> None:
        self.calls = 0
        self._stop_event = stop_event
        self._failures = failures

    async def run_once(self) -> InboxBatchResult:
        self.calls += 1
        if self.calls <= self._failures:
            raise RuntimeError("db down")
        self._stop_event.set()
        return _result()


async def test_polling_worker_runs_task_and_stops() -> None:
    stop_event = asyncio.Event()
    task = StoppingTask(stop_event)

    await run_polling_worker(task, interval_seconds=0, stop_event=stop_event)

    assert task.calls == 1


async def test_worker_survives_transient_failure_and_backs_off() -> None:
    stop_event = asyncio.Event()
    task = FailingTask(stop_event, failures=2)
    worker = PollingWorker(
        task,
        PollingWorkerConfig(poll_interval_seconds=0, error_backoff_seconds=0),
    )

    await worker.run(stop_event)

    assert task.calls == 3


async def test_worker_does_not_start_batch_after_shutdown() -> None:
    stop_event = asyncio.Event()
    task = StoppingTask(stop_event)
    worker = PollingWorker(task, PollingWorkerConfig(poll_interval_seconds=0))

    await worker.run(stop_event)

    assert task.calls == 1
