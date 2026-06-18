from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.dto.dto import GraphNodeExecutionResultDto
    from shell.application.ports.queries import GraphNodeExecutionResultQueryService
    from shell.application.queries.queries import GetGraphNodeExecutionResultQuery


class GetGraphNodeExecutionResultHandler:
    def __init__(self, queries: GraphNodeExecutionResultQueryService) -> None:
        self._queries = queries

    async def handle(
        self, query: GetGraphNodeExecutionResultQuery
    ) -> GraphNodeExecutionResultDto | None:
        return await self._queries.get_graph_node_execution_result(
            query.graph_node_execution_id, query.workflow_id
        )
