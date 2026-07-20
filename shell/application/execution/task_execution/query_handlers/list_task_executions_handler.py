from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.task_execution.dto.task_execution import (
        TaskExecutionDto,
    )
    from shell.application.execution.task_execution.ports.task_execution_query_service import (
        TaskExecutionQueryService,
    )
    from shell.application.execution.task_execution.queries.list_task_executions_query import (
        ListTaskExecutionsQuery,
    )


class ListTaskExecutionsHandler:
    def __init__(self, queries: TaskExecutionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: ListTaskExecutionsQuery) -> tuple[list[TaskExecutionDto], int]:
        return await self._queries.list_all(page=query.page, page_size=query.page_size)
