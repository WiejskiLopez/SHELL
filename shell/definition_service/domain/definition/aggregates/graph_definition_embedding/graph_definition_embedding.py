from __future__ import annotations

from typing import TYPE_CHECKING

from shell.definition_service.domain.definition.aggregates.graph_definition_embedding.events.graph_definition_embedding_changed_event import (
    GraphDefinitionEmbeddingChangedEvent,
)
from shell.definition_service.domain.definition.aggregates.graph_definition_embedding.events.graph_definition_embedding_deleted_event import (
    GraphDefinitionEmbeddingDeletedEvent,
)
from shell.definition_service.domain.definition.aggregates.graph_definition_embedding.value_objects.embedding_text import (
    EmbeddingText,
)
from shell.definition_service.domain.definition.aggregates.graph_definition_embedding.value_objects.graph_definition_embedding_id import (
    GraphDefinitionEmbeddingId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt

if TYPE_CHECKING:
    from shell.definition_service.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.definition_service.domain.definition.aggregates.graph_definition_embedding.value_objects.embedding import (
        Embedding,
    )
    from shell.definition_service.domain.definition.aggregates.graph_definition_embedding.value_objects.embedding_model import (
        EmbeddingModel,
    )


from shell.definition_service.domain.definition.aggregates.graph_definition_embedding.events.graph_definition_embedding_created_event import (
    GraphDefinitionEmbeddingCreatedEvent,
)


class GraphDefinitionEmbedding(AggregateRoot[GraphDefinitionEmbeddingId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
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
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
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
        self._changed_at = changed_at
        self._deleted_at = deleted_at

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
        return cls._new(
            id=id,
            graph_definition_id=graph_definition_id,
            text=text,
            embedding=embedding,
            model=model,
            now=OccurredAt.from_datetime(now.value),
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            GraphDefinitionEmbeddingDeletedEvent.now(
                graph_definition_embedding_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            GraphDefinitionEmbeddingChangedEvent.now(
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
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def changed_at(self) -> ChangedAt:
        return self._changed_at

    @classmethod
    def restore(
        cls,
        *,
        id: GraphDefinitionEmbeddingId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
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
            changed_at=changed_at,
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
