from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution_state.value_objects.node_execution_state_id import (
        NodeExecutionStateId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class NodeExecutionStateDeletedEvent(DomainEvent):
    node_execution_state_id: NodeExecutionStateId

    @classmethod
    def now(
        cls, node_execution_state_id: NodeExecutionStateId, now: OccurredAt
    ) -> NodeExecutionStateDeletedEvent:
        return cls(occurred_at=now, node_execution_state_id=node_execution_state_id)
