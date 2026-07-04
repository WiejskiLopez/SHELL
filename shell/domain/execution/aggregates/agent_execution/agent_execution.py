from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import (
    AgentExecutionId,
)
from shell.domain.platform.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )


class AgentExecution(AggregateRoot[AgentExecutionId]):
    __slots__ = ("_node_execution_id",)

    _node_execution_id: NodeExecutionId

    def __init__(
        self,
        id_: AgentExecutionId,
        node_execution_id: NodeExecutionId,
    ) -> None:
        super().__init__(id_)
        self._node_execution_id = node_execution_id

    @classmethod
    def restore(
        cls,
        id_: AgentExecutionId,
        node_execution_id: NodeExecutionId,
    ) -> Self:
        return cls(
            id_=id_,
            node_execution_id=node_execution_id,
        )

    @property
    def node_execution_id(self) -> NodeExecutionId:
        return self._node_execution_id
