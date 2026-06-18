from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Iterable

    from shell.domain.entities.graph_execution import GraphExecution
    from shell.domain.entities.graph_node_execution import GraphNodeExecution
    from shell.domain.value_objects.ids import GraphNodeExecutionId


class NodeNavigator(Protocol):
    """Decides the next node(s) to execute in a Graph."""

    def first(self, graph_execution: GraphExecution) -> GraphNodeExecution | None:
        ...

    def next_after(
        self, graph_execution: GraphExecution, graph_node_execution_id: GraphNodeExecutionId
    ) -> Iterable[GraphNodeExecution]:
        ...
