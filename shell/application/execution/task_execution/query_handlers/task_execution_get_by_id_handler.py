from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.task_execution.dto.task_execution import TaskExecutionDto
    from shell.application.execution.task_execution.ports.task_execution_query_service import (
        TaskExecutionQueryService,
    )
    from shell.application.execution.task_execution.queries.task_execution_get_by_id_query import (
        TaskExecutionGetByIdQuery,
    )


class TaskExecutionGetByIdHandler:
    def __init__(self, queries: TaskExecutionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: TaskExecutionGetByIdQuery) -> TaskExecutionDto | None:
        return await self._queries.get_by_id(query.task_execution_id)
