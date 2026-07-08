from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.user_execution.dto.user_execution import UserExecutionDto
    from shell.application.execution.user_execution.ports.user_execution_query_service import (
        UserExecutionQueryService,
    )
    from shell.application.execution.user_execution.queries.user_execution_get_by_id_query import (
        UserExecutionGetByIdQuery,
    )


class UserExecutionGetByIdHandler:
    def __init__(self, queries: UserExecutionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: UserExecutionGetByIdQuery) -> UserExecutionDto | None:
        return await self._queries.get_by_id(query.user_execution_id)
