from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_input import (
        GraphNodeExecutionStateInput,
    )
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )
    from shell.domain.execution.value_objects.exists_result import ExistsResult


class GraphNodeExecutionStateInputRepository(Protocol):
    async def get_latest_by_node_id(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> GraphNodeExecutionStateInput | None: ...

    async def delete(self, id: object) -> None: ...
    async def exists(self, id: object) -> ExistsResult: ...
    
    async def save(self, payload: GraphNodeExecutionStateInput) -> None: ...
    async def delete(self, id: object) -> None: ...
    async def exists(self, id: object) -> ExistsResult: ...
    