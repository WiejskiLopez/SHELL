from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution.value_objects.NodeExecutionId import (
        NodeExecutionId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class NodeExecutionUpdatedEvent(DomainEvent):
    nodeexecution_id: NodeExecutionId

    @classmethod
    def now(cls, nodeexecution_id: NodeExecutionId, now: CreatedAt) -> NodeExecutionUpdatedEvent:
        return cls(occurred_at=now, nodeexecution_id=nodeexecution_id)
