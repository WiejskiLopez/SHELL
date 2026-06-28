from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.dto.graph_node_execution_result import GraphNodeExecutionResultDto
    from shell.application.platform.ports.queries import GraphNodeExecutionResultQueryService
    from shell.application.execution.queries.graph_node_execution_get_result_query import GraphNodeExecutionGetResultQuery


class GraphNodeExecutionGetResultHandler:
    def __init__(self, queries: GraphNodeExecutionResultQueryService) -> None:
        self._queries = queries

    async def handle(
        self, get_graph_node_execution_result_query: GetGraphNodeExecutionResultQuery
    ) -> GraphNodeExecutionResultDto | None:
        return await self._queries.get_graph_node_execution_result(
            get_graph_node_execution_result_query.graph_node_execution_id, get_graph_node_execution_result_query.workflow_id
        )
