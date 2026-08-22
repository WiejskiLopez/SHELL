"""Runtime helper for standalone bounded-context event inbox workers."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from shell.platform.infrastructure.messaging.polling_worker import (
    PollingWorker,
    PollingWorkerConfig,
)
from shell.platform.infrastructure.messaging.worker_heartbeat import WorkerHeartbeatRecorder

if TYPE_CHECKING:
    from collections.abc import Sequence


async def run_delivery_workers(
    *,
    workers: Sequence[tuple[Any, Any, str]],
    session_factory: Any,
    heartbeat_model: type[Any],
    poll_interval_seconds: float,
    outbox_relay: Any | None = None,
    outbox_worker_id: str = "outbox-relay",
) -> None:
    """Run multiple inbox workers and close all consumers on shutdown."""
    for consumer, _, _ in workers:
        await consumer.start()
    try:
        tasks = []
        for _, processor, worker_id in workers:
            heartbeat = WorkerHeartbeatRecorder(session_factory, heartbeat_model, worker_id)
            tasks.append(
                PollingWorker(
                    processor,
                    PollingWorkerConfig(
                        worker_id=worker_id,
                        poll_interval_seconds=poll_interval_seconds,
                    ),
                    heartbeat=heartbeat.beat,
                ).run()
            )
        if outbox_relay is not None:
            heartbeat = WorkerHeartbeatRecorder(
                session_factory,
                heartbeat_model,
                outbox_worker_id,
            )
            tasks.append(
                PollingWorker(
                    outbox_relay,
                    PollingWorkerConfig(
                        worker_id=outbox_worker_id,
                        poll_interval_seconds=poll_interval_seconds,
                    ),
                    heartbeat=heartbeat.beat,
                ).run()
            )
        await asyncio.gather(*tasks)
    finally:
        for consumer, _, _ in workers:
            await consumer.close()


async def run_event_inbox_worker(
    *,
    consumer: Any,
    processor: Any,
    session_factory: Any,
    heartbeat_model: type[Any],
    worker_id: str,
    poll_interval_seconds: float,
) -> None:
    """Run one BC event consumer and processor with a stable heartbeat."""
    await run_delivery_workers(
        workers=((consumer, processor, worker_id),),
        session_factory=session_factory,
        heartbeat_model=heartbeat_model,
        poll_interval_seconds=poll_interval_seconds,
    )
