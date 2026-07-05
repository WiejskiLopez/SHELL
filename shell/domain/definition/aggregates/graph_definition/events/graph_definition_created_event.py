from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.value_objects.graph_name import GraphName
    from shell.domain.definition.value_objects.purpose import Purpose
    from shell.domain.platform.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class GraphDefinitionCreatedEvent(DomainEvent):
    graph_definition_id: GraphDefinitionId
    name: GraphName
    purpose: Purpose

    @classmethod
    def now(
        cls,
        graph_definition_id: GraphDefinitionId,
        name: GraphName,
        purpose: Purpose,
        now: CreatedAt,
    ) -> GraphDefinitionCreatedEvent:
        return cls(
            occurred_at=now,
            graph_definition_id=graph_definition_id,
            name=name,
            purpose=purpose,
        )
