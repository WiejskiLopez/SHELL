from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.definition_service.domain.definition.aggregates.graph_definition_embedding.value_objects.graph_definition_embedding_id import (
        GraphDefinitionEmbeddingId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class GraphDefinitionEmbeddingChangedEvent(DomainEvent):
    graph_definition_embedding_id: GraphDefinitionEmbeddingId

    @classmethod
    def now(
        cls, graph_definition_embedding_id: GraphDefinitionEmbeddingId, now: OccurredAt
    ) -> GraphDefinitionEmbeddingChangedEvent:
        return cls(occurred_at=now, graph_definition_embedding_id=graph_definition_embedding_id)
