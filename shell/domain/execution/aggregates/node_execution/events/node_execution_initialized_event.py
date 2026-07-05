from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.domain.execution.value_objects.node_definition_id import NodeDefinitionId
    from shell.domain.platform.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class NodeExecutionInitializedEvent(DomainEvent):
    node_id: NodeExecutionId
    graph_execution_id: GraphExecutionId
    node_definition_id: NodeDefinitionId

    @classmethod
    def now(
        cls,
        node_id: NodeExecutionId,
        graph_execution_id: GraphExecutionId,
        node_definition_id: NodeDefinitionId,
        now: CreatedAt,
    ) -> NodeExecutionInitializedEvent:
        return cls(
            occurred_at=now,
            node_id=node_id,
            graph_execution_id=graph_execution_id,
            node_definition_id=node_definition_id,
        )
