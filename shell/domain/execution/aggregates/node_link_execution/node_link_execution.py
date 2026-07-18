from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.node_link_execution.value_objects.node_link_execution_id import (
    NodeLinkExecutionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )

class NodeLinkExecution(AggregateRoot[NodeLinkExecutionId]):
    __slots__ = (
        "_updated_at",
        "_created_at",
        "_graph_execution_id",
        "_node_execution_id",
    )

    def __init__(
        self,
        id: NodeLinkExecutionId,
        graph_execution_id: GraphExecutionId,
        node_execution_id: NodeExecutionId,
    ) -> None:
        super().__init__(id)
        self._graph_execution_id = graph_execution_id
        self._node_execution_id = node_execution_id

    @classmethod
    def create(
        cls,
        *,
        id_: NodeLinkExecutionId,
        graph_execution_id: GraphExecutionId,
        node_execution_id: NodeExecutionId,
    ) -> NodeLinkExecution:
        return cls(
            id=id_,
            graph_execution_id=graph_execution_id,
            node_execution_id=node_execution_id,
        )

    @classmethod
    def restore(
        cls,
        id: NodeLinkExecutionId,
        graph_execution_id: GraphExecutionId,
        node_execution_id: NodeExecutionId,
    ) -> Self:
        return cls(
            id=id,
            graph_execution_id=graph_execution_id,
            node_execution_id=node_execution_id,
        )

    def _delete(self) -> None:
        raise NotImplementedError("_delete() not yet implemented")

    @property
    def graph_execution_id(self) -> GraphExecutionId:
        return self._graph_execution_id

    @property
    def node_execution_id(self) -> NodeExecutionId:
        return self._node_execution_id
