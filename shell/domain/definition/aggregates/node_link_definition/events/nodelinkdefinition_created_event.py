from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.nodelinkdefinition.aggregates.nodelinkdefinition.value_objects.NodeLinkDefinitionId import NodeLinkDefinitionId
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class NodeLinkDefinitionCreatedEvent(DomainEvent):
    nodelinkdefinition_id: NodeLinkDefinitionId

    @classmethod
    def now(cls, nodelinkdefinition_id: NodeLinkDefinitionId, now: CreatedAt) -> "NodeLinkDefinitionCreatedEvent":
        return cls(occurred_at=now, nodelinkdefinition_id=nodelinkdefinition_id)
