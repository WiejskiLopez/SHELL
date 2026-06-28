from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.platform.dto import TaskExecutionDto
    from shell.application.platform.ports.queries import TaskExecutionQueryService
    from shell.application.platform.queries.queries import GetCurrentTaskExecutionQuery


class GetCurrentTaskExecutionHandler:
    def __init__(self, queries: TaskExecutionQueryService) -> None:
        self._queries = queries

    async def handle(self, get_current_task_execution_query: GetCurrentTaskExecutionQuery) -> TaskExecutionDto | None:
        return await self._queries.get_current_task(get_current_task_execution_query.name)
