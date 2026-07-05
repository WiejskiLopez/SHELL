from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.definition.value_objects.chunk_index import ChunkIndex
    from shell.domain.definition.value_objects.embedding_model import EmbeddingModel
    from shell.domain.definition.value_objects.ids import RagDocumentId
    from shell.domain.platform.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class RagDocumentChunksAddedEvent(DomainEvent):
    document_id: RagDocumentId
    chunk_count: ChunkIndex
    model: EmbeddingModel

    @classmethod
    def now(
        cls,
        document_id: RagDocumentId,
        chunk_count: ChunkIndex,
        model: EmbeddingModel,
        now: CreatedAt,
    ) -> RagDocumentChunksAddedEvent:
        return cls(occurred_at=now, document_id=document_id, chunk_count=chunk_count, model=model)
