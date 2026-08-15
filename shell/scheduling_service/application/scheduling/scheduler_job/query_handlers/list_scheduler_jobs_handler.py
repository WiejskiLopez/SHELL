from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.scheduling_service.application.scheduling.scheduler_job.dto.scheduler_job import (
        SchedulerJobDto,
    )
    from shell.scheduling_service.application.scheduling.scheduler_job.ports.scheduler_job_query_service import (
        SchedulerJobQueryService,
    )
    from shell.scheduling_service.application.scheduling.scheduler_job.queries.list_scheduler_jobs_query import (
        ListSchedulerJobsQuery,
    )


class ListSchedulerJobsHandler:
    def __init__(self, queries: SchedulerJobQueryService) -> None:
        self._queries = queries

    async def handle(
        self, query: ListSchedulerJobsQuery
    ) -> tuple[list[SchedulerJobDto], int] | None:
        return await self._queries.list_all()
