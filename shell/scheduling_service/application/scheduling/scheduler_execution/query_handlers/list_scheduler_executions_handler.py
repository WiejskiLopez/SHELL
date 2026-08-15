from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.scheduling_service.application.scheduling.scheduler_execution.dto.scheduler_execution import (
        SchedulerExecutionDto,
    )
    from shell.scheduling_service.application.scheduling.scheduler_execution.ports.scheduler_execution_query_service import (
        SchedulerExecutionQueryService,
    )
    from shell.scheduling_service.application.scheduling.scheduler_execution.queries.list_scheduler_executions_query import (
        ListSchedulerExecutionsQuery,
    )


class ListSchedulerExecutionsHandler:
    def __init__(self, queries: SchedulerExecutionQueryService) -> None:
        self._queries = queries

    async def handle(
        self, query: ListSchedulerExecutionsQuery
    ) -> tuple[list[SchedulerExecutionDto], int] | None:
        return await self._queries.list_all()
