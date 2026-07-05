from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
    from shell.domain.platform.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class NodeExecutionAdvancedEvent(DomainEvent):
    workflow_id: WorkflowId
    from_node_execution_id: NodeExecutionId
    to_node_execution_id: NodeExecutionId

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        from_node_execution_id: NodeExecutionId,
        to_node_execution_id: NodeExecutionId,
        now: CreatedAt,
    ) -> NodeExecutionAdvancedEvent:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            from_node_execution_id=from_node_execution_id,
            to_node_execution_id=to_node_execution_id,
        )
