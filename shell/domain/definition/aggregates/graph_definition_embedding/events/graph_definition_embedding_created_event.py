from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_definition_embedding.value_objects.graph_definition_embedding_id import (
        GraphDefinitionEmbeddingId,
    )
    from shell.domain.definition.value_objects.embedding import Embedding
    from shell.domain.definition.value_objects.embedding_model import EmbeddingModel
    from shell.domain.definition.value_objects.embedding_text import EmbeddingText
    from shell.domain.platform.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class GraphDefinitionEmbeddingCreatedEvent(DomainEvent):
    graph_definition_embedding_id: GraphDefinitionEmbeddingId
    graph_definition_id: GraphDefinitionId
    text: EmbeddingText
    embedding: Embedding
    embedding_model: EmbeddingModel

    @classmethod
    def now(
        cls,
        graph_definition_embedding_id: GraphDefinitionEmbeddingId,
        graph_definition_id: GraphDefinitionId,
        text: EmbeddingText,
        embedding: Embedding,
        embedding_model: EmbeddingModel,
        now: CreatedAt,
    ) -> GraphDefinitionEmbeddingCreatedEvent:
        return cls(
            occurred_at=now,
            graph_definition_embedding_id=graph_definition_embedding_id,
            graph_definition_id=graph_definition_id,
            text=text,
            embedding=embedding,
            embedding_model=embedding_model,
        )
