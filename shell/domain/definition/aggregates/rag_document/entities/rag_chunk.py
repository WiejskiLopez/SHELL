from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.value_objects.chunk_index import ChunkIndex
from shell.domain.definition.value_objects.chunk_text import ChunkText
from shell.domain.definition.value_objects.embedding import Embedding
from shell.domain.definition.value_objects.embedding_model import EmbeddingModel
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
        chunk_index: ChunkIndex,
        chunk_text: ChunkText,
        embedding: Embedding,
        embedding_model: EmbeddingModel,
    ) -> None:
        super().__init__(id)
        self._document_id = document_id
        self._chunk_index = (
            chunk_index if isinstance(chunk_index, ChunkIndex) else ChunkIndex(chunk_index)
        )
        self._chunk_text = (
            chunk_text if isinstance(chunk_text, ChunkText) else ChunkText(chunk_text)
        )
        self._embedding = embedding if isinstance(embedding, Embedding) else Embedding(embedding)
        self._embedding_model = (
            embedding_model
            if isinstance(embedding_model, EmbeddingModel)
            else EmbeddingModel(embedding_model)
        )

    @property
    def document_id(self) -> RagDocumentId:
        return self._document_id

    @property
    def chunk_index(self) -> ChunkIndex:
        return self._chunk_index

    @property
    def chunk_text(self) -> ChunkText:
        return self._chunk_text

    @property
    def embedding(self) -> Embedding:
        return self._embedding

    @property
    def embedding_model(self) -> EmbeddingModel:
        return self._embedding_model
