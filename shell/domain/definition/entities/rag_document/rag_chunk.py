from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.ids import RagChunkId, RagDocumentId


@dataclass(slots=True)
class RagChunk:
    id: RagChunkId
    document_id: RagDocumentId
    chunk_index: int
    chunk_text: str
    embedding: bytes
    embedding_model: str

    def __post_init__(self) -> None:
        if self.chunk_index < 0:
            raise ValueError("chunk_index must be >= 0")
        if not self.chunk_text:
            raise ValueError("chunk_text cannot be empty")
        if not self.embedding_model:
            raise ValueError("embedding_model cannot be empty")
