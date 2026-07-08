from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.scheduling.scheduler_execution.dto.scheduler_execution import (
        SchedulerExecutionDto,
    )
    from shell.application.scheduling.scheduler_execution.ports.scheduler_execution_query_service import (
        SchedulerExecutionQueryService,
    )
    from shell.application.scheduling.scheduler_execution.queries.scheduler_execution_get_by_id_query import (
        SchedulerExecutionGetByIdQuery,
    )


class SchedulerExecutionGetByIdHandler:
    def __init__(self, queries: SchedulerExecutionQueryService) -> None:
        self._queries = queries

    async def handle(
        self, query: SchedulerExecutionGetByIdQuery
    ) -> SchedulerExecutionDto | None:
        return await self._queries.get_by_id(query.scheduler_execution_id)
