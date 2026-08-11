from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.execution.domain.execution.aggregates.node_execution.node_execution import (
        NodeExecution,
    )
    from shell.execution.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.platform.domain.value_objects.exists_result import ExistsResult


class NodeExecutionRepository(Protocol):
    async def get_by_id(self, node_id: NodeExecutionId) -> NodeExecution | None: ...

    async def delete(self, id: NodeExecutionId) -> None: ...
    async def exists(self, id: NodeExecutionId) -> ExistsResult: ...

    async def save(self, node: NodeExecution) -> None: ...

    async def list_by_ids(self, ids: list[NodeExecutionId]) -> list[NodeExecution]: ...

    async def list_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> list[NodeExecution]: ...

    async def get_next_pending(
        self, graph_execution_id: GraphExecutionId
    ) -> NodeExecution | None: ...
