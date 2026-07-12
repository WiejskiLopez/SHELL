from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.domain.execution.aggregates.node_execution_state.value_objects.node_execution_state_id import (
        NodeExecutionStateId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class NodeExecutionStateChangedEvent(DomainEvent):
    node_execution_id: NodeExecutionId
    node_execution_state_id: NodeExecutionStateId

    @classmethod
    def now(
        cls,
        node_execution_id: NodeExecutionId,
        node_execution_state_id: NodeExecutionStateId,
        now: CreatedAt,
    ) -> NodeExecutionStateChangedEvent:
        return cls(
            occurred_at=now,
            node_execution_id=node_execution_id,
            node_execution_state_id=node_execution_state_id,
        )
