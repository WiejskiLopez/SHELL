from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.state_data import StateData

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.domain.execution.aggregates.workflow.value_objects.node_execution_result_id import (
        NodeExecutionResultId,
    )
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
    from shell.domain.platform.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class NodeExecutionCompletedEvent(DomainEvent):
    node_id: NodeExecutionId
    role: NodeRole
    result: StateData
    workflow_id: WorkflowId | None = None
    result_id: NodeExecutionResultId | None = None

    @property
    def node_execution_id(self) -> NodeExecutionId:
        return self.node_id

    @classmethod
    def now(
        cls,
        node_id: NodeExecutionId,
        now: CreatedAt,
        role: NodeRole | None = None,
        result: StateData | None = None,
        workflow_id: WorkflowId | None = None,
        result_id: NodeExecutionResultId | None = None,
    ) -> NodeExecutionCompletedEvent:
        return cls(
            occurred_at=now,
            node_id=node_id,
            role=role or NodeRole.AGENT,
            result=result if result is not None else StateData(value={}),
            workflow_id=workflow_id,
            result_id=result_id,
        )
