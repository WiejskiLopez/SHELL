from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.definition.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class GraphDefinitionCreatedEvent(DomainEvent):
    graph_definition_id: GraphDefinitionId

    @classmethod
    def now(
        cls,
        graph_definition_id: GraphDefinitionId,
        now: OccurredAt,
    ) -> GraphDefinitionCreatedEvent:
        return cls(
            occurred_at=now,
            graph_definition_id=graph_definition_id,
        )
