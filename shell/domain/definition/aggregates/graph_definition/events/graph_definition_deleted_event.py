from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.GraphDefinitionId import (
        GraphDefinitionId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class GraphDefinitionDeletedEvent(DomainEvent):
    graphdefinition_id: GraphDefinitionId

    @classmethod
    def now(cls, graphdefinition_id: GraphDefinitionId, now: CreatedAt) -> GraphDefinitionDeletedEvent:
        return cls(occurred_at=now, graphdefinition_id=graphdefinition_id)
