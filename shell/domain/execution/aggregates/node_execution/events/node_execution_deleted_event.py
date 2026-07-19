from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class NodeExecutionDeletedEvent(DomainEvent):
    node_execution_id: NodeExecutionId

    @classmethod
    def now(cls, node_execution_id: NodeExecutionId, now: OccurredAt) -> NodeExecutionDeletedEvent:
        return cls(occurred_at=now, node_execution_id=node_execution_id)
