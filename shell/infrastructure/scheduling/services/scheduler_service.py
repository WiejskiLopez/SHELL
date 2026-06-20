"""APScheduler-based cyclic job runner.

Replaces the old MessagingWorker loop.
Jobs are defined by SchedulerExecution rows in the DB.
On start, loads all enabled SchedulerExecution rows and registers
them as APScheduler interval jobs.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from shell.infrastructure.scheduling.persistence.sql.repositories.sql_scheduler_execution_repository import (
    SqlSchedulerExecutionRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.domain.scheduling.aggregates.scheduler_execution import (
        SchedulerExecution,
    )
    from shell.domain.scheduling.value_objects.ids import SchedulerExecutionId
    from shell.infrastructure.platform.messaging.outbox_to_inbox_relay import (
        OutboxToInboxRelay,
    )
    from shell.infrastructure.platform.messaging.processor.inbox_processor import (
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
            executions = await repo.list_enabled()

        for execution in executions:
            self._add_job(execution)

        self._scheduler.start()
        self._running = True
        logger.info(
            "scheduler_service.started",
            extra={"job_count": len(executions)},
        )

    def stop(self) -> None:
        if self._running:
            self._scheduler.shutdown(wait=False)
            self._running = False
            logger.info("scheduler_service.stopped")

    def add_job(self, execution: SchedulerExecution) -> None:
        self._add_job(execution)

    def remove_job(self, execution_id: SchedulerExecutionId) -> None:
        job_id = _JOB_ID_PREFIX + execution_id.value
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
            logger.info(
                "scheduler_service.job_removed",
                extra={"execution_id": execution_id.value},
            )

    def _add_job(self, execution: SchedulerExecution) -> None:
        if not execution.enabled:
            return

        job_id = _JOB_ID_PREFIX + execution.id.value

        if self._scheduler.get_job(job_id):
            self._scheduler.reschedule_job(
                job_id,
                trigger=IntervalTrigger(seconds=execution.interval_seconds),
            )
            return

        job_fn = _build_job_fn(
            job_type=execution.job_type,
            outbox_relay=self._outbox_to_inbox_relay,
            inbox_processor=self._inbox_processor,
        )

        self._scheduler.add_job(
            job_fn,
            trigger=IntervalTrigger(seconds=execution.interval_seconds),
            id=job_id,
            name=execution.name or execution.id.value,
            replace_existing=True,
        )
        logger.info(
            "scheduler_service.job_added",
            extra={
                "execution_id": execution.id.value,
                "job_type": execution.job_type,
                "interval": execution.interval_seconds,
            },
        )


def _build_job_fn(
    *,
    job_type: str,
    outbox_relay: OutboxToInboxRelay,
    inbox_processor: InboxProcessor,
):
    if job_type == "messaging":
        async def _run() -> None:
            try:
                await outbox_relay.run_once()
                await inbox_processor.run_once()
            except Exception:
                logger.exception("scheduler_service.job_error")

        return _run

    raise ValueError(f"Unknown job_type: {job_type}")
