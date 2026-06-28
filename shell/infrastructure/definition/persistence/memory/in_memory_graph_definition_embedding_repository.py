from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_definition_embedding.graph_definition_embedding import (
    GraphDefinitionEmbedding,
)
from shell.domain.definition.aggregates.graph_definition_embedding.repositories import (
    GraphDefinitionEmbeddingRepository,
)
from shell.domain.definition.aggregates.graph_definition_embedding.value_objects import (
    GraphDefinitionEmbeddingId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )


class InMemoryGraphDefinitionEmbeddingRepository(
    InMemoryRepository[GraphDefinitionEmbedding, GraphDefinitionEmbeddingId],
    GraphDefinitionEmbeddingRepository,
):

    async def save(self, embedding: GraphDefinitionEmbedding) -> None:
        self._store[embedding.id.value] = embedding

    async def get_by_graph_definition_id(
        self, graph_definition_id: GraphDefinitionId,
    ) -> GraphDefinitionEmbedding | None:
        for emb in self._store.values():
            if emb.graph_definition_id == graph_definition_id:
                return emb
        return None
