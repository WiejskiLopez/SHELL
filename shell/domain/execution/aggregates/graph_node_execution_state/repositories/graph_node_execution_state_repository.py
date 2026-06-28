from __future__ import annotations

from typing import Protocol

from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution_state.graph_node_execution_state import (
    GraphNodeExecutionState,
)
from shell.domain.execution.aggregates.graph_node_execution_state.value_objects.graph_node_execution_state_id import (
    GraphNodeExecutionStateId,
)
from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.domain.execution.value_objects.state_direction import StateDirection


class GraphNodeExecutionStateRepository(Protocol):
    async def get_by_id(
        self, id_: GraphNodeExecutionStateId
    ) -> GraphNodeExecutionState | None: ...

    async def list_by_graph_node_execution_id(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> list[GraphNodeExecutionState]: ...

    async def list_by_graph_node_execution_and_direction(
        self, graph_node_execution_id: GraphNodeExecutionId, direction: StateDirection
    ) -> list[GraphNodeExecutionState]: ...

    async def save(self, state: GraphNodeExecutionState) -> None: ...

    async def delete(self, id_: GraphNodeExecutionStateId) -> None: ...

    async def exists(self, id_: GraphNodeExecutionStateId) -> ExistsResult: ...
