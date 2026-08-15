from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.execution_service.application.execution.task_execution.dto.task_execution import (
        TaskExecutionDto,
    )
    from shell.execution_service.application.execution.task_execution.ports.task_execution_query_service import (
        TaskExecutionQueryService,
    )
    from shell.execution_service.application.execution.task_execution.queries import (
        GetTaskExecutionByNameQuery,
    )


class GetTaskExecutionByNameHandler:
    def __init__(self, queries: TaskExecutionQueryService) -> None:
        self._queries = queries

    async def handle(
        self, get_task_execution_by_name_query: GetTaskExecutionByNameQuery
    ) -> TaskExecutionDto | None:
        return await self._queries.get_task_execution_by_name(get_task_execution_by_name_query.name)
