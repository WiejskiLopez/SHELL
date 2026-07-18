from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.nodelinkexecution.aggregates.nodelinkexecution.value_objects.NodeLinkExecutionId import NodeLinkExecutionId
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class NodeLinkExecutionCreatedEvent(DomainEvent):
    nodelinkexecution_id: NodeLinkExecutionId

    @classmethod
    def now(cls, nodelinkexecution_id: NodeLinkExecutionId, now: CreatedAt) -> "NodeLinkExecutionCreatedEvent":
        return cls(occurred_at=now, nodelinkexecution_id=nodelinkexecution_id)
