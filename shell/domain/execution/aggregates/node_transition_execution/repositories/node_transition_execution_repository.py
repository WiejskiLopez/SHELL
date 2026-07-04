from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.domain.execution.aggregates.node_transition_execution.node_transition_execution import (
        NodeTransitionExecution,
    )
    from shell.domain.execution.aggregates.node_transition_execution.value_objects.node_transition_execution_id import (
        NodeTransitionExecutionId,
    )
    from shell.domain.platform.value_objects.exists_result import ExistsResult


class NodeTransitionExecutionRepository(Protocol):
    async def get_by_id(
        self, id_: NodeTransitionExecutionId
    ) -> NodeTransitionExecution | None: ...

    async def delete(self, id: object) -> None: ...
    async def exists(self, id: object) -> ExistsResult: ...

    async def list_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> list[NodeTransitionExecution]: ...

    async def list_outgoing_for_node(
        self, node_id: NodeExecutionId
    ) -> list[NodeTransitionExecution]: ...

    async def save(self, transition: NodeTransitionExecution) -> None: ...
