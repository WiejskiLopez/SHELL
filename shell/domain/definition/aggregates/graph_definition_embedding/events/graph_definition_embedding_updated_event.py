from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition_embedding.value_objects.GraphDefinitionEmbeddingId import (
        GraphDefinitionEmbeddingId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class GraphDefinitionEmbeddingUpdatedEvent(DomainEvent):
    graphdefinitionembedding_id: GraphDefinitionEmbeddingId

    @classmethod
    def now(cls, graphdefinitionembedding_id: GraphDefinitionEmbeddingId, now: CreatedAt) -> GraphDefinitionEmbeddingUpdatedEvent:
        return cls(occurred_at=now, graphdefinitionembedding_id=graphdefinitionembedding_id)
