from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.edge_execution.value_objects.edge_definition_id_ref import (
        EdgeDefinitionIdRef,
    )
    from shell.execution.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
        EdgeExecutionId,
    )
    from shell.execution.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class EdgeExecutionCreatedEvent(DomainEvent):
    edge_execution_id: EdgeExecutionId
    edge_definition_id: EdgeDefinitionIdRef
    source_node_execution_id: NodeExecutionId
    target_node_execution_id: NodeExecutionId | None

    @classmethod
    def now(
        cls,
        edge_execution_id: EdgeExecutionId,
        edge_definition_id: EdgeDefinitionIdRef,
        source_node_execution_id: NodeExecutionId,
        target_node_execution_id: NodeExecutionId | None,
        now: OccurredAt,
    ) -> EdgeExecutionCreatedEvent:
        return cls(
            occurred_at=now,
            edge_execution_id=edge_execution_id,
            edge_definition_id=edge_definition_id,
            source_node_execution_id=source_node_execution_id,
            target_node_execution_id=target_node_execution_id,
        )
