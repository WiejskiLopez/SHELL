from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.value_objects.ids import RagChunkId
from shell.domain.platform.base.entity import Entity

if TYPE_CHECKING:
    from shell.domain.definition.value_objects.ids import RagDocumentId


class RagChunk(Entity[RagChunkId]):
    __slots__ = ("_document_id", "_chunk_index", "_chunk_text", "_embedding", "_embedding_model")

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
        self._document_id = document_id
        self._chunk_index = chunk_index
        self._chunk_text = chunk_text
        self._embedding = embedding
        self._embedding_model = embedding_model

    @property
    def document_id(self) -> RagDocumentId:
        return self._document_id

    @property
    def chunk_index(self) -> int:
        return self._chunk_index

    @property
    def chunk_text(self) -> str:
        return self._chunk_text

    @property
    def embedding(self) -> bytes:
        return self._embedding

    @property
    def embedding_model(self) -> str:
        return self._embedding_model
