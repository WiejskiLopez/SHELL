from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution_state.value_objects.node_execution_state_id import (
        NodeExecutionStateId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt

@dataclass(frozen=True, slots=True)
class NodeExecutionStateUpdatedEvent(DomainEvent):
    nodeexecutionstate_id: NodeExecutionStateId

    @classmethod
    def now(cls, nodeexecutionstate_id: NodeExecutionStateId, now: CreatedAt) -> NodeExecutionStateUpdatedEvent:
        return cls(occurred_at=now, nodeexecutionstate_id=nodeexecutionstate_id)
