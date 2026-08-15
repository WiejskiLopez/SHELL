from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.definition_service.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.definition_service.domain.definition.aggregates.graph_definition_embedding.graph_definition_embedding import (
    GraphDefinitionEmbedding,
)
from shell.definition_service.domain.definition.aggregates.graph_definition_embedding.repositories import (
    GraphDefinitionEmbeddingRepository,
)
from shell.definition_service.domain.definition.aggregates.graph_definition_embedding.value_objects.embedding import (
    Embedding,
)
from shell.definition_service.domain.definition.aggregates.graph_definition_embedding.value_objects.embedding_model import (
    EmbeddingModel,
)
from shell.definition_service.domain.definition.aggregates.graph_definition_embedding.value_objects.embedding_text import (
    EmbeddingText,
)
from shell.definition_service.domain.definition.aggregates.graph_definition_embedding.value_objects.graph_definition_embedding_id import (
    GraphDefinitionEmbeddingId,
)
from shell.definition_service.infrastructure.definition.graph_definition_embedding.persistence.sql.models.graph_definition_embedding import (
    GraphDefinitionEmbeddingModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlGraphDefinitionEmbeddingRepository(GraphDefinitionEmbeddingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self,
        id: GraphDefinitionEmbeddingId,
    ) -> GraphDefinitionEmbedding | None:
        model = await self._session.get(GraphDefinitionEmbeddingModel, id.value)
        if model is None:
            return None
        return GraphDefinitionEmbedding(
            id=GraphDefinitionEmbeddingId(model.id),
            graph_definition_id=GraphDefinitionId(model.graph_definition_id),
            text=EmbeddingText(model.text),
            embedding=Embedding(model.embedding),
            model=EmbeddingModel(model.embedding_model),
            created_at=CreatedAt.now(),
        )

    async def get_by_graph_definition_id(
        self,
        graph_definition_id: GraphDefinitionId,
    ) -> GraphDefinitionEmbedding | None:
        stmt = select(GraphDefinitionEmbeddingModel).where(
            GraphDefinitionEmbeddingModel.graph_definition_id == graph_definition_id.value,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return GraphDefinitionEmbedding(
            id=GraphDefinitionEmbeddingId(model.id),
            graph_definition_id=graph_definition_id,
            text=EmbeddingText(model.text),
            embedding=Embedding(model.embedding),
            model=EmbeddingModel(model.embedding_model),
            created_at=CreatedAt.now(),
        )

    async def save(self, embedding: GraphDefinitionEmbedding) -> None:
        model = await self._session.get(
            GraphDefinitionEmbeddingModel,
            embedding.id.value,
        )
        if model is None:
            model = GraphDefinitionEmbeddingModel(
                id=embedding.id.value,
                graph_definition_id=embedding.graph_definition_id.value,
                text=embedding.text.value,
                embedding=embedding.embedding.value,
                embedding_model=embedding.model.value,
            )
            self._session.add(model)
        else:
            model.text = embedding.text.value
            model.embedding = embedding.embedding.value
            model.embedding_model = embedding.model.value

    async def delete(self, id: GraphDefinitionEmbeddingId, now: datetime | None = None) -> None:
        if now is None:
            now = datetime.now(tz=UTC)
        model = await self._session.get(GraphDefinitionEmbeddingModel, id.value)
        if model is not None:
            model.deleted_at = now
