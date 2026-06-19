from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.entities.base.entity import Entity

if TYPE_CHECKING:
    from shell.domain.value_objects.ids import RagChunkId, RagDocumentId


class RagChunk(Entity[RagChunkId]):
    __slots__ = ("document_id", "chunk_index", "chunk_text", "embedding", "embedding_model")

    def __init__(
        self,
        id: RagChunkId,
        document_id: RagDocumentId,
        chunk_index: int,
        chunk_text: str,
        embedding: bytes,
        embedding_model: str,
    ) -> None:
        if chunk_index < 0:
            raise ValueError("chunk_index must be >= 0")
        if not chunk_text:
            raise ValueError("chunk_text cannot be empty")
        if not embedding_model:
            raise ValueError("embedding_model cannot be empty")
        super().__init__(id)
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.chunk_text = chunk_text
        self.embedding = embedding
        self.embedding_model = embedding_model
