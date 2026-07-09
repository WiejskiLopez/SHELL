from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.scheduling.scheduler_execution.dto.scheduler_execution import (
        SchedulerExecutionDto,
    )
    from shell.application.scheduling.scheduler_execution.ports.scheduler_execution_query_service import (
        SchedulerExecutionQueryService,
    )
    from shell.application.scheduling.scheduler_execution.queries.get_scheduler_execution_by_id_query import (
        GetSchedulerExecutionByIdQuery,
    )


class GetSchedulerExecutionByIdHandler:
    def __init__(self, queries: SchedulerExecutionQueryService) -> None:
        self._queries = queries

    async def handle(
        self, query: GetSchedulerExecutionByIdQuery
    ) -> SchedulerExecutionDto | None:
        return await self._queries.get_by_id(query.scheduler_execution_id)
