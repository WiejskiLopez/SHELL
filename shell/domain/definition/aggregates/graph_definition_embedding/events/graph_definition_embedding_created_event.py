from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from shell.domain.definition.aggregates.graph_definition_embedding.value_objects.graph_definition_embedding_id import (
    GraphDefinitionEmbeddingId,
)
from shell.domain.definition.value_objects.embedding import Embedding
from shell.domain.definition.value_objects.embedding_model import EmbeddingModel
from shell.domain.definition.value_objects.embedding_text import EmbeddingText
from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )


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
        now: datetime,
    ) -> GraphDefinitionEmbeddingCreatedEvent:
        return cls(
            occurred_at=now,
            graph_definition_embedding_id=graph_definition_embedding_id,
            graph_definition_id=graph_definition_id,
            text=text,
            embedding=embedding,
            embedding_model=embedding_model,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
            GraphDefinitionId,
        )

        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_definition_embedding_id=GraphDefinitionEmbeddingId(payload.get("graph_definition_embedding_id", "")),
            graph_definition_id=GraphDefinitionId(payload.get("graph_definition_id", "")),
            text=EmbeddingText(payload.get("text", "")),
            embedding=Embedding(bytes(payload.get("embedding", b""))),
            embedding_model=EmbeddingModel(payload.get("embedding_model", "")),
        )
