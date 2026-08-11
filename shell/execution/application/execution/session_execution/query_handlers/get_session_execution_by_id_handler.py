from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.execution.application.execution.session_execution.dto.session_execution import (
        SessionExecutionDto,
    )
    from shell.execution.application.execution.session_execution.ports.session_execution_query_service import (
        SessionExecutionQueryService,
    )
    from shell.execution.application.execution.session_execution.queries.get_session_execution_by_id_query import (
        GetSessionExecutionByIdQuery,
    )


class GetSessionExecutionByIdHandler:
    def __init__(self, queries: SessionExecutionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetSessionExecutionByIdQuery) -> SessionExecutionDto | None:
        return await self._queries.get_by_id(query.session_execution_id)
