from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import AgentExecutionId
from shell.domain.platform.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )


class AgentExecution(AggregateRoot[AgentExecutionId]):
    __slots__ = ("_graph_node_execution_id",)

    _graph_node_execution_id: GraphNodeExecutionId

    def __init__(
        self,
        id_: AgentExecutionId,
        graph_node_execution_id: GraphNodeExecutionId,
    ) -> None:
        super().__init__(id_)
        self._graph_node_execution_id = graph_node_execution_id

    @classmethod
    def restore(
        cls,
        id_: AgentExecutionId,
        graph_node_execution_id: GraphNodeExecutionId,
    ) -> Self:
        return cls(
            id_=id_,
            graph_node_execution_id=graph_node_execution_id,
        )

    @property
    def graph_node_execution_id(self) -> GraphNodeExecutionId:
        return self._graph_node_execution_id
