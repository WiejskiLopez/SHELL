from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_definition_embedding.value_objects.embedding_text import (
    EmbeddingText,
)
from shell.domain.definition.aggregates.graph_definition_embedding.value_objects.graph_definition_embedding_id import (
    GraphDefinitionEmbeddingId,
)
from shell.domain.platform.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_definition_embedding.value_objects.embedding import (
        Embedding,
    )
    from shell.domain.definition.aggregates.graph_definition_embedding.value_objects.embedding_model import (
        EmbeddingModel,
    )
    from shell.domain.platform.value_objects.created_at import CreatedAt


from shell.domain.definition.aggregates.graph_definition_embedding.events.graph_definition_embedding_created_event import (
    GraphDefinitionEmbeddingCreatedEvent,
)


class GraphDefinitionEmbedding(AggregateRoot[GraphDefinitionEmbeddingId]):
    __slots__ = (
        "_graph_definition_id",
        "_text",
        "_embedding",
        "_model",
        "_created_at",
        "_updated_at",
    )

    def __init__(
        self,
        id: GraphDefinitionEmbeddingId,
        graph_definition_id: GraphDefinitionId,
        text: EmbeddingText,
        embedding: Embedding,
        model: EmbeddingModel,
        created_at: CreatedAt | None = None,
        updated_at: CreatedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._graph_definition_id = graph_definition_id
        self._text = text if isinstance(text, EmbeddingText) else EmbeddingText(text)
        self._embedding = embedding
        self._model = model
        self._created_at = created_at
        self._updated_at = updated_at

    @classmethod
    def restore(
        cls,
        id: GraphDefinitionEmbeddingId,
        graph_definition_id: GraphDefinitionId,
        text: EmbeddingText,
        embedding: Embedding,
        model: EmbeddingModel,
        created_at: CreatedAt | None = None,
        updated_at: CreatedAt | None = None,
    ) -> GraphDefinitionEmbedding:
        return cls(
            id=id,
            graph_definition_id=graph_definition_id,
            text=text,
            embedding=embedding,
            model=model,
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def create(
        cls,
        id: GraphDefinitionEmbeddingId,
        graph_definition_id: GraphDefinitionId,
        text: EmbeddingText,
        embedding: Embedding,
        model: EmbeddingModel,
        now: CreatedAt,
    ) -> GraphDefinitionEmbedding:
        instance = cls(
            id=id,
            graph_definition_id=graph_definition_id,
            text=text,
            embedding=embedding,
            model=model,
            created_at=now,
            updated_at=now,
        )
        instance.append_event(
            GraphDefinitionEmbeddingCreatedEvent.now(
                graph_definition_embedding_id=id,
                graph_definition_id=graph_definition_id,
                text=EmbeddingText(str(text)),
                embedding=embedding,
                embedding_model=model,
                now=now,
            )
        )
        return instance

    @property
    def graph_definition_id(self) -> GraphDefinitionId:
        return self._graph_definition_id

    @property
    def text(self) -> EmbeddingText:
        return self._text

    @property
    def embedding(self) -> Embedding:
        return self._embedding

    @property
    def model(self) -> EmbeddingModel:
        return self._model

    @property
    def created_at(self) -> CreatedAt | None:
        return self._created_at

    @property
    def updated_at(self) -> CreatedAt | None:
        return self._updated_at
