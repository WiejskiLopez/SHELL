from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.graph_node_link_execution.value_objects.graph_node_link_execution_id import (
    GraphNodeLinkExecutionId,
)
from shell.domain.platform.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )


class GraphNodeLinkExecution(AggregateRoot[GraphNodeLinkExecutionId]):
    __slots__ = (
        "_graph_execution_id",
        "_graph_node_execution_id",
    )

    def __init__(
        self,
        id: GraphNodeLinkExecutionId,
        graph_execution_id: GraphExecutionId,
        graph_node_execution_id: GraphNodeExecutionId,
    ) -> None:
        super().__init__(id)
        self._graph_execution_id = graph_execution_id
        self._graph_node_execution_id = graph_node_execution_id

    @classmethod
    def restore(
        cls,
        id: GraphNodeLinkExecutionId,
        graph_execution_id: GraphExecutionId,
        graph_node_execution_id: GraphNodeExecutionId,
    ) -> Self:
        return cls(
            id=id,
            graph_execution_id=graph_execution_id,
            graph_node_execution_id=graph_node_execution_id,
        )

    @property
    def graph_execution_id(self) -> GraphExecutionId:
        return self._graph_execution_id

    @property
    def graph_node_execution_id(self) -> GraphNodeExecutionId:
        return self._graph_node_execution_id
