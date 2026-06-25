from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_output import (
        GraphNodeExecutionStateOutput,
    )
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )


class GraphNodeExecutionStateOutputRepository(Protocol):
    async def get_latest_by_node_id(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> GraphNodeExecutionStateOutput | None: ...

    async def delete(self, id: object) -> None: ...
    async def exists(self, id: object) -> bool: ...
    
    async def save(self, payload: GraphNodeExecutionStateOutput) -> None: ...
    async def delete(self, id: object) -> None: ...
    async def exists(self, id: object) -> bool: ...
    