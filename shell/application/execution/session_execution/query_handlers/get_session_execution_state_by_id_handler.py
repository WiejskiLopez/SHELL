from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.session_execution.dto.session_execution_state import (
        SessionExecutionStateDto,
    )
    from shell.application.execution.session_execution.ports.session_execution_state_query_service import (
        SessionExecutionStateQueryService,
    )
    from shell.application.execution.session_execution.queries.get_session_execution_state_by_id_query import (
        GetSessionExecutionStateByIdQuery,
    )


class GetSessionExecutionStateByIdHandler:
    def __init__(self, queries: SessionExecutionStateQueryService) -> None:
        self._queries = queries

    async def handle(
        self, query: GetSessionExecutionStateByIdQuery
    ) -> SessionExecutionStateDto | None:
        return await self._queries.get_by_id(query.session_execution_state_id)
