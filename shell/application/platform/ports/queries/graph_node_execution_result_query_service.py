from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.execution.dto.graph_node_execution_result import (
        GraphNodeExecutionResultDto,
    )


class GraphNodeExecutionResultQueryService(Protocol):
    async def get_graph_node_execution_result(
        self, graph_node_execution_id: str, workflow_id: str
    ) -> GraphNodeExecutionResultDto | None: ...
