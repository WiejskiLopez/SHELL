from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.node_definition.value_objects.NodeDefinitionId import (
        NodeDefinitionId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class NodeDefinitionUpdatedEvent(DomainEvent):
    nodedefinition_id: NodeDefinitionId

    @classmethod
    def now(cls, nodedefinition_id: NodeDefinitionId, now: CreatedAt) -> NodeDefinitionUpdatedEvent:
        return cls(occurred_at=now, nodedefinition_id=nodedefinition_id)
