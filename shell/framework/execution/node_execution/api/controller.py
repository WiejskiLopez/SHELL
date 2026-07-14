from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.application.execution.node_execution.queries.get_node_execution_result_query import (
    GetNodeExecutionResultQuery,
)
from shell.framework.execution.node_execution.api.node_execution_result_response import (
    NodeExecutionResultResponse,
)

if TYPE_CHECKING:
    from shell.platform.application.bus.query_bus import QueryBus


class NodeExecutionController:
    __slots__ = ("_query_bus",)

    def __init__(self, query_bus: QueryBus) -> None:
        self._query_bus = query_bus

    async def get_node_execution_result(
        self, node_execution_id: str, workflow_id: str
    ) -> NodeExecutionResultResponse:
        result = await self._query_bus.dispatch(
            GetNodeExecutionResultQuery(
                node_execution_id=node_execution_id, workflow_id=workflow_id
            )
        )
        if result is None:
            raise HTTPException(
                status_code=404, detail=f"NodeResult for '{node_execution_id}' not found"
            )
        return NodeExecutionResultResponse(
            node_execution_id=node_execution_id,
            workflow_id=workflow_id,
            status=str(result),
        )
