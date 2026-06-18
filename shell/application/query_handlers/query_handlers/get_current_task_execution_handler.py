from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.dto.dto import TaskExecutionDto
    from shell.application.ports.queries import TaskExecutionQueryService
    from shell.application.queries.queries import GetCurrentTaskExecutionQuery


class GetCurrentTaskExecutionHandler:
    def __init__(self, queries: TaskExecutionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetCurrentTaskExecutionQuery) -> TaskExecutionDto | None:
        return await self._queries.get_current_task(query.name)
