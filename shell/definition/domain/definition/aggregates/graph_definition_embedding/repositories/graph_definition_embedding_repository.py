from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.definition.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.definition.domain.definition.aggregates.graph_definition_embedding.graph_definition_embedding import (
        GraphDefinitionEmbedding,
    )
    from shell.definition.domain.definition.aggregates.graph_definition_embedding.value_objects.graph_definition_embedding_id import (
        GraphDefinitionEmbeddingId,
    )
    from shell.platform.domain.value_objects.exists_result import ExistsResult


class GraphDefinitionEmbeddingRepository(Protocol):
    async def get_by_id(
        self, id: GraphDefinitionEmbeddingId
    ) -> GraphDefinitionEmbedding | None: ...

    async def get_by_graph_definition_id(
        self,
        graph_definition_id: GraphDefinitionId,
    ) -> GraphDefinitionEmbedding | None: ...

    async def save(self, embedding: GraphDefinitionEmbedding) -> None: ...

    async def delete(self, id: GraphDefinitionEmbeddingId) -> None: ...

    async def exists(self, id: GraphDefinitionEmbeddingId) -> ExistsResult: ...
