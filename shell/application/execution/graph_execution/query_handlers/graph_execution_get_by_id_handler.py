from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.graph_execution.dto.graph_execution import (
        GraphExecutionDto,
    )
    from shell.application.execution.graph_execution.ports.graph_execution_query_service import (
        GraphExecutionQueryService,
    )
    from shell.application.execution.graph_execution.queries.graph_execution_get_by_id_query import (
        GraphExecutionGetByIdQuery,
    )


class GraphExecutionGetByIdHandler:
    def __init__(self, queries: GraphExecutionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GraphExecutionGetByIdQuery) -> GraphExecutionDto | None:
        return await self._queries.get_by_id(query.graph_execution_id)
