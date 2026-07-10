from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.edge_execution.value_objects.edge_definition_id import (
        EdgeDefinitionId,
    )
    from shell.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
        EdgeExecutionId,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class EdgeExecutionCreatedEvent(DomainEvent):
    edge_execution_id: EdgeExecutionId
    edge_definition_id: EdgeDefinitionId
    source_node_execution_id: NodeExecutionId
    target_node_execution_id: NodeExecutionId | None

    @classmethod
    def now(
        cls,
        edge_execution_id: EdgeExecutionId,
        edge_definition_id: EdgeDefinitionId,
        source_node_execution_id: NodeExecutionId,
        target_node_execution_id: NodeExecutionId | None,
        now: CreatedAt,
    ) -> EdgeExecutionCreatedEvent:
        return cls(
            occurred_at=now,
            edge_execution_id=edge_execution_id,
            edge_definition_id=edge_definition_id,
            source_node_execution_id=source_node_execution_id,
            target_node_execution_id=target_node_execution_id,
        )
