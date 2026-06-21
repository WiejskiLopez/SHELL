from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_execution import GraphNodeExecution
    from shell.domain.execution.value_objects.ids import GraphExecutionId, GraphNodeExecutionId


class GraphNodeExecutionRepository(Protocol):
    async def get_by_id(self, node_id: GraphNodeExecutionId) -> GraphNodeExecution | None: ...

    async def save(self, node: GraphNodeExecution) -> None: ...

    async def list_by_ids(self, ids: list[GraphNodeExecutionId]) -> list[GraphNodeExecution]: ...

    async def list_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> list[GraphNodeExecution]: ...
