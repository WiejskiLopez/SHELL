from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.execution.application.execution.node_execution.dto.node_execution_result import (
        NodeExecutionResultDto,
    )
    from shell.execution.application.execution.node_execution.ports.node_execution_result_query_service import (
        NodeExecutionResultQueryService,
    )
    from shell.execution.application.execution.node_execution.queries.get_node_execution_result_query import (
        GetNodeExecutionResultQuery,
    )


class GetNodeExecutionResultHandler:
    def __init__(self, queries: NodeExecutionResultQueryService) -> None:
        self._queries = queries

    async def handle(
        self, get_node_execution_result_query: GetNodeExecutionResultQuery
    ) -> NodeExecutionResultDto | None:
        return await self._queries.get_node_execution_result(
            get_node_execution_result_query.node_execution_id,
            get_node_execution_result_query.workflow_id,
        )
