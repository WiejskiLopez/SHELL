from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Iterable

    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
        GraphNodeExecution,
    )
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )
    from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
        GraphNodeExecutionRepository,
    )
    from shell.domain.execution.aggregates.graph_node_transition_execution.repositories.graph_node_transition_execution_repository import (
        GraphNodeTransitionExecutionRepository,
    )


class GraphNodeExecutionNavigator(Protocol):
    """Decides the next node(s) to execute in a Graph."""

    async def first_async(
        self,
        graph_execution: GraphExecution,
        node_repo: GraphNodeExecutionRepository,
        transition_repo: GraphNodeTransitionExecutionRepository,
    ) -> GraphNodeExecution | None: ...

    async def next_after_async(
        self,
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        node_repo: GraphNodeExecutionRepository,
        transition_repo: GraphNodeTransitionExecutionRepository,
    ) -> Iterable[GraphNodeExecution]: ...
