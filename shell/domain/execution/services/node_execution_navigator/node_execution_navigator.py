from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Iterable

    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.node_execution.node_execution import (
        NodeExecution,
    )
    from shell.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
        NodeExecutionRepository,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.domain.execution.aggregates.node_transition_execution.repositories.node_transition_execution_repository import (
        NodeTransitionExecutionRepository,
    )


class NodeExecutionNavigator(Protocol):
    """Decides the next node(s) to execute in a Graph."""

    async def first_async(
        self,
        graph_execution: GraphExecution,
        node_repo: NodeExecutionRepository,
        transition_repo: NodeTransitionExecutionRepository,
    ) -> NodeExecution | None: ...

    async def next_after_async(
        self,
        graph_execution: GraphExecution,
        node_execution_id: NodeExecutionId,
        node_repo: NodeExecutionRepository,
        transition_repo: NodeTransitionExecutionRepository,
    ) -> Iterable[NodeExecution]: ...
