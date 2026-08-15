from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.execution_service.domain.execution.aggregates.node_execution_state.value_objects.node_execution_state_id import (
        NodeExecutionStateId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class NodeExecutionStateChangedEvent(DomainEvent):
    node_execution_id: NodeExecutionId
    node_execution_state_id: NodeExecutionStateId

    @classmethod
    def now(
        cls,
        node_execution_id: NodeExecutionId,
        node_execution_state_id: NodeExecutionStateId,
        now: OccurredAt,
    ) -> NodeExecutionStateChangedEvent:
        return cls(
            occurred_at=now,
            node_execution_id=node_execution_id,
            node_execution_state_id=node_execution_state_id,
        )
