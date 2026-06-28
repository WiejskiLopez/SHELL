from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.dto.task_execution import TaskExecutionDto
    from shell.application.platform.ports.queries import TaskExecutionQueryService
    from shell.application.execution.queries.task_execution_queries import TaskExecutionGetCurrentQuery


class TaskExecutionGetCurrentHandler:
    def __init__(self, queries: TaskExecutionQueryService) -> None:
        self._queries = queries

    async def handle(self, get_current_task_execution_query: GetCurrentTaskExecutionQuery) -> TaskExecutionDto | None:
        return await self._queries.get_current_task(get_current_task_execution_query.name)
