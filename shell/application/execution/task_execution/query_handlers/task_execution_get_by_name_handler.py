from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.task_execution.dto.task_execution import TaskExecutionDto
    from shell.application.execution.task_execution.queries import (
        TaskExecutionGetByNameQuery,
    )
    from shell.application.platform.ports.queries import TaskExecutionQueryService


class TaskExecutionGetByNameHandler:
    def __init__(self, queries: TaskExecutionQueryService) -> None:
        self._queries = queries

    async def handle(
        self, get_task_execution_by_name_query: TaskExecutionGetByNameQuery
    ) -> TaskExecutionDto | None:
        return await self._queries.get_task_execution_by_name(get_task_execution_by_name_query.name)
