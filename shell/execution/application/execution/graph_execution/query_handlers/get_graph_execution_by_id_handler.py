from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.execution.application.execution.graph_execution.dto.graph_execution import (
        GraphExecutionDto,
    )
    from shell.execution.application.execution.graph_execution.ports.graph_execution_query_service import (
        GraphExecutionQueryService,
    )
    from shell.execution.application.execution.graph_execution.queries.get_graph_execution_by_id_query import (
        GetGraphExecutionByIdQuery,
    )


class GetGraphExecutionByIdHandler:
    def __init__(self, queries: GraphExecutionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetGraphExecutionByIdQuery) -> GraphExecutionDto | None:
        return await self._queries.get_by_id(query.graph_execution_id)
