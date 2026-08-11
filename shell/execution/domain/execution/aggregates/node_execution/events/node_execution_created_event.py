from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.execution.domain.execution.aggregates.node_execution.value_objects.node_definition_id_ref import (
        NodeDefinitionIdRef,
    )
    from shell.execution.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class NodeExecutionCreatedEvent(DomainEvent):
    node_execution_id: NodeExecutionId
    node_definition_id: NodeDefinitionIdRef | None
    graph_execution_id: GraphExecutionId | None

    @classmethod
    def now(
        cls,
        *,
        node_execution_id: NodeExecutionId,
        node_definition_id: NodeDefinitionIdRef | None,
        graph_execution_id: GraphExecutionId | None,
        now: OccurredAt,
    ) -> NodeExecutionCreatedEvent:
        return cls(
            occurred_at=now,
            node_execution_id=node_execution_id,
            node_definition_id=node_definition_id,
            graph_execution_id=graph_execution_id,
        )
