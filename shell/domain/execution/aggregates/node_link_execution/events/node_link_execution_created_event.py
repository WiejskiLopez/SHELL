from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.domain.execution.aggregates.node_link_execution.value_objects.node_link_execution_id import (
        NodeLinkExecutionId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class NodeLinkExecutionCreatedEvent(DomainEvent):
    node_link_execution_id: NodeLinkExecutionId
    graph_execution_id: GraphExecutionId
    node_execution_id: NodeExecutionId

    @classmethod
    def now(
        cls,
        node_link_execution_id: NodeLinkExecutionId,
        graph_execution_id: GraphExecutionId,
        node_execution_id: NodeExecutionId,
        now: CreatedAt,
    ) -> NodeLinkExecutionCreatedEvent:
        return cls(
            occurred_at=now,
            node_link_execution_id=node_link_execution_id,
            graph_execution_id=graph_execution_id,
            node_execution_id=node_execution_id,
        )
