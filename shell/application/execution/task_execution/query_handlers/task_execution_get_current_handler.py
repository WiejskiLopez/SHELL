from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.task_execution.dto.task_execution import TaskExecutionDto
    from shell.application.execution.task_execution.ports.task_execution_query_service import (
        TaskExecutionQueryService,
    )
    from shell.application.execution.task_execution.queries import (
        TaskExecutionGetCurrentQuery,
    )


class TaskExecutionGetCurrentHandler:
    def __init__(self, queries: TaskExecutionQueryService) -> None:
        self._queries = queries

    async def handle(
        self, get_current_task_execution_query: TaskExecutionGetCurrentQuery
    ) -> TaskExecutionDto | None:
        return await self._queries.get_current_task(get_current_task_execution_query.name)
