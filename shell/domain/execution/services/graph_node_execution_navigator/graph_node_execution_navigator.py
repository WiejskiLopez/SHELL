from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Iterable

    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
        GraphNodeExecution,
    )
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution_id import (
        GraphNodeExecutionId,
    )
    from shell.domain.execution.aggregates.graph_node_execution.ports.graph_node_execution_repository import (
        GraphNodeExecutionRepository,
    )


class GraphNodeExecutionNavigator(Protocol):
    """Decides the next node(s) to execute in a Graph."""

    def first(self, graph_execution: GraphExecution) -> GraphNodeExecution | None: ...

    def next_after(
        self, graph_execution: GraphExecution, graph_node_execution_id: GraphNodeExecutionId
    ) -> Iterable[GraphNodeExecution]: ...

    async def first_async(
        self,
        graph_execution: GraphExecution,
        node_repo: GraphNodeExecutionRepository,
    ) -> GraphNodeExecution | None: ...

    async def next_after_async(
        self,
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        node_repo: GraphNodeExecutionRepository,
    ) -> Iterable[GraphNodeExecution]: ...
