from __future__ import annotations

from typing import Protocol

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.aggregates.graph_node_transition_execution.graph_node_transition_execution import (
    GraphNodeTransitionExecution,
)
from shell.domain.execution.aggregates.graph_node_transition_execution.value_objects.graph_node_transition_execution_id import (
    GraphNodeTransitionExecutionId,
)
from shell.domain.platform.value_objects.exists_result import ExistsResult


class GraphNodeTransitionExecutionRepository(Protocol):
    async def get_by_id(
        self, id_: GraphNodeTransitionExecutionId
    ) -> GraphNodeTransitionExecution | None: ...

    async def delete(self, id: object) -> None: ...
    async def exists(self, id: object) -> ExistsResult: ...

    async def list_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> list[GraphNodeTransitionExecution]: ...

    async def list_outgoing_for_node(
        self, node_id: GraphNodeExecutionId
    ) -> list[GraphNodeTransitionExecution]: ...

    async def save(
        self, transition: GraphNodeTransitionExecution
    ) -> None: ...
