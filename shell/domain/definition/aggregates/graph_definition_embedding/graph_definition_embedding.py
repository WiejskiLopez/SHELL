from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_definition_embedding.events.graph_definition_embedding_deleted_event import (
    GraphDefinitionEmbeddingDeletedEvent,
)
from shell.domain.definition.aggregates.graph_definition_embedding.events.graph_definition_embedding_updated_event import (
    GraphDefinitionEmbeddingUpdatedEvent,
)
from shell.domain.definition.aggregates.graph_definition_embedding.value_objects.embedding_text import (
    EmbeddingText,
)
from shell.domain.definition.aggregates.graph_definition_embedding.value_objects.graph_definition_embedding_id import (
    GraphDefinitionEmbeddingId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

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


from shell.domain.definition.aggregates.graph_definition_embedding.events.graph_definition_embedding_created_event import (
    GraphDefinitionEmbeddingCreatedEvent,
)


class GraphDefinitionEmbedding(AggregateRoot[GraphDefinitionEmbeddingId]):
    __slots__ = (
        "_created_at",
        "_updated_at",
        "_deleted_at",
        "_graph_definition_id",
        "_text",
        "_embedding",
        "_model",
    )

    def __init__(
        self,
        *,
        id: GraphDefinitionEmbeddingId,
        created_at: CreatedAt,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
        graph_definition_id: GraphDefinitionId,
        text: EmbeddingText,
        embedding: Embedding,
        model: EmbeddingModel,
    ) -> None:
        super().__init__(id)
        self._graph_definition_id = graph_definition_id
        self._text = text if isinstance(text, EmbeddingText) else EmbeddingText(text)
        self._embedding = embedding
        self._model = model
        self._created_at = created_at
        self._updated_at = UpdatedAt(value=None) if updated_at is None else updated_at
        self._deleted_at = DeletedAt(value=None) if deleted_at is None else deleted_at

    @classmethod
    def create(
        cls,
        id: GraphDefinitionEmbeddingId,
        now: CreatedAt,
        graph_definition_id: GraphDefinitionId,
        text: EmbeddingText,
        embedding: Embedding,
        model: EmbeddingModel,
    ) -> GraphDefinitionEmbedding:
        instance = cls(
            id=id,
            graph_definition_id=graph_definition_id,
            text=text,
            embedding=embedding,
            model=model,
            created_at=CreatedAt.from_datetime(now.value),
            updated_at=UpdatedAt.from_datetime(now.value),
        )
        instance.append_event(
            GraphDefinitionEmbeddingCreatedEvent.now(
                graph_definition_embedding_id=id,
                graph_definition_id=graph_definition_id,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            GraphDefinitionEmbeddingDeletedEvent.now(
                graph_definition_embedding_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _update(self, now: CreatedAt) -> None:
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            GraphDefinitionEmbeddingUpdatedEvent.now(
                graph_definition_embedding_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

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
    def updated_at(self) -> UpdatedAt:
        return self._updated_at

    @classmethod
    def restore(
        cls,
        *,
        id: GraphDefinitionEmbeddingId,
        created_at: CreatedAt,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
        graph_definition_id: GraphDefinitionId,
        text: EmbeddingText,
        embedding: Embedding,
        model: EmbeddingModel,
    ) -> GraphDefinitionEmbedding:
        return cls(
            id=id,
            graph_definition_id=graph_definition_id,
            text=text,
            embedding=embedding,
            model=model,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

    @classmethod
    def _new(
        cls,
        id: GraphDefinitionEmbeddingId,
        now: OccurredAt,
        graph_definition_id: GraphDefinitionId,
        text: EmbeddingText,
        embedding: Embedding,
        model: EmbeddingModel,
    ) -> GraphDefinitionEmbedding:
        instance = cls(
            id=id,
            graph_definition_id=graph_definition_id,
            text=text,
            embedding=embedding,
            model=model,
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            GraphDefinitionEmbeddingCreatedEvent.now(
                graph_definition_embedding_id=id,
                graph_definition_id=graph_definition_id,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance
