from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.definition.value_objects.chunk_index import ChunkIndex
from shell.domain.definition.value_objects.embedding_model import EmbeddingModel
from shell.domain.definition.value_objects.ids import RagDocumentId
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class RagDocumentChunksAddedEvent(DomainEvent):
    document_id: RagDocumentId
    chunk_count: ChunkIndex
    model: EmbeddingModel

    @classmethod
    def now(cls, document_id: RagDocumentId, chunk_count: ChunkIndex, model: EmbeddingModel, now: datetime) -> RagDocumentChunksAddedEvent:
        return cls(occurred_at=now, document_id=document_id, chunk_count=chunk_count, model=model)

    @classmethod
    def from_payload(cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            document_id=RagDocumentId(payload["document_id"]),
            chunk_count=ChunkIndex(payload.get("chunk_count", 0)),
            model=EmbeddingModel(payload.get("model", "")),
        )
