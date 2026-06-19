from typing import Protocol

from shell.application.dto import GraphNodeExecutionResultDto


class GraphNodeExecutionResultQueryService(Protocol):
    """Port do sprawdzania wyników wykonania konkretnych węzłów."""

    async def get_graph_node_execution_result(
        self, graph_node_execution_id: str, workflow_id: str
    ) -> GraphNodeExecutionResultDto | None: ...
