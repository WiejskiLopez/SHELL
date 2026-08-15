from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
        EdgeExecutionId,
    )
    from shell.execution_service.domain.execution.aggregates.edge_link_execution.value_objects.edge_link_execution_id import (
        EdgeLinkExecutionId,
    )
    from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class EdgeLinkExecutionCreatedEvent(DomainEvent):
    edge_link_execution_id: EdgeLinkExecutionId
    node_execution_id: NodeExecutionId
    edge_execution_id: EdgeExecutionId

    @classmethod
    def now(
        cls,
        edge_link_execution_id: EdgeLinkExecutionId,
        node_execution_id: NodeExecutionId,
        edge_execution_id: EdgeExecutionId,
        now: OccurredAt,
    ) -> EdgeLinkExecutionCreatedEvent:
        return cls(
            occurred_at=now,
            edge_link_execution_id=edge_link_execution_id,
            node_execution_id=node_execution_id,
            edge_execution_id=edge_execution_id,
        )
