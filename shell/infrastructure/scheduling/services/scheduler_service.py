"""APScheduler-based cyclic job runner (future: mozna zastapic asyncio.Task).

Replaces the old MessagingWorker loop.
Jobs are defined by SchedulerExecution rows in the DB.
On start, loads all enabled SchedulerExecution rows and registers
them as APScheduler interval jobs.

Future consideration: jesli funkcjonalnosc scheduler_a nie wzrosnie
(outbox relay + inbox processor), mozna zastapic apscheduler prostym
``asyncio.Task`` + ``asyncio.sleep(interval)`` i usunac zaleznosc.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore[import-untyped]

from shell.infrastructure.scheduling.scheduler_execution.persistence.sql.repositories.sql_scheduler_execution_repository import (
    SqlSchedulerExecutionRepository,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id import (
        SchedulerExecutionId,
    )
    from shell.domain.scheduling.aggregates.scheduler_job.scheduler_job import (
        SchedulerJob,
    )
    from shell.platform.infrastructure.messaging.event.outbox_to_inbox_relay import (
        OutboxToInboxRelay,
    )
    from shell.platform.infrastructure.messaging.event.processor.inbox_processor import (
        InboxProcessor,
    )

logger = logging.getLogger(__name__)

_JOB_ID_PREFIX = "scheduler_execution_"


class SchedulerService:
    """Manages cyclic jobs via APScheduler."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        outbox_to_inbox_relay: OutboxToInboxRelay,
        inbox_processor: InboxProcessor,
    ) -> None:
        self._session_factory = session_factory
        self._outbox_to_inbox_relay = outbox_to_inbox_relay
        self._inbox_processor = inbox_processor
        self._scheduler = AsyncIOScheduler()
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    async def start(self) -> None:
        """Load enabled executions from DB and register APScheduler jobs."""
        async with self._session_factory() as session:
            repo = SqlSchedulerExecutionRepository(session)
            jobs = await repo.list_enabled()

        for job in jobs:
            self._add_job(job)

        self._scheduler.start()
        self._running = True
        logger.info(
            "scheduler_service.started",
            extra={"job_count": len(jobs)},
        )

    def stop(self) -> None:
        if self._running:
            self._scheduler.shutdown(wait=False)
            self._running = False
            logger.info("scheduler_service.stopped")

    def add_job(self, job: SchedulerJob) -> None:
        self._add_job(job)

    def remove_job(self, job_id_value: SchedulerExecutionId) -> None:
        job_id = _JOB_ID_PREFIX + job_id_value.value
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
            logger.info(
                "scheduler_service.job_removed",
                extra={"job_id": job_id_value.value},
            )

    def _add_job(self, job: SchedulerJob) -> None:
        if not job.enabled.value:
            return

        job_id = _JOB_ID_PREFIX + job.id.value

        if self._scheduler.get_job(job_id):
            self._scheduler.reschedule_job(
                job_id,
                trigger=IntervalTrigger(seconds=int(job.interval_seconds.value)),
            )
            return

        job_fn = _build_job_fn(
            job_type=job.job_type.value,
            outbox_relay=self._outbox_to_inbox_relay,
            inbox_processor=self._inbox_processor,
        )

        self._scheduler.add_job(
            job_fn,
            trigger=IntervalTrigger(seconds=int(job.interval_seconds.value)),
            id=job_id,
            name=job.name.value,
            replace_existing=True,
        )
        logger.info(
            "scheduler_service.job_added",
            extra={
                "job_id": job.id.value,
                "job_type": job.job_type.value,
                "interval": job.interval_seconds.value,
            },
        )


def _build_job_fn(
    *,
    job_type: str,
    outbox_relay: OutboxToInboxRelay,
    inbox_processor: InboxProcessor,
) -> Callable[[], Awaitable[None]]:
    if job_type == "messaging":

        async def _run() -> None:
            try:
                await outbox_relay.run_once()
                await inbox_processor.run_once()
            except Exception:
                logger.exception("scheduler_service.job_error")

        return _run

    raise ValueError(f"Unknown job_type: {job_type}")
