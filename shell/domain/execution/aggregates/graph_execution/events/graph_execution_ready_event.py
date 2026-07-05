from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.value_objects.node_definition_execution_slot import (
        NodeDefinitionExecutionSlot,
    )
    from shell.domain.platform.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class GraphExecutionReadyEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    node_definition_executions: tuple[NodeDefinitionExecutionSlot, ...] = field(
        default_factory=tuple
    )

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        node_definition_executions: list[NodeDefinitionExecutionSlot],
        now: CreatedAt,
    ) -> GraphExecutionReadyEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            node_definition_executions=tuple(node_definition_executions),
        )
