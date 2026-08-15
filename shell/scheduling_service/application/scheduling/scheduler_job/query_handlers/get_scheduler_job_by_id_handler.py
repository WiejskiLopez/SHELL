from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.scheduling_service.application.scheduling.scheduler_job.dto.scheduler_job import (
        SchedulerJobDto,
    )
    from shell.scheduling_service.application.scheduling.scheduler_job.ports.scheduler_job_query_service import (
        SchedulerJobQueryService,
    )
    from shell.scheduling_service.application.scheduling.scheduler_job.queries.get_scheduler_job_by_id_query import (
        GetSchedulerJobByIdQuery,
    )


class GetSchedulerJobByIdHandler:
    def __init__(self, queries: SchedulerJobQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetSchedulerJobByIdQuery) -> SchedulerJobDto | None:
        return await self._queries.get_by_id(query.scheduler_job_id)
