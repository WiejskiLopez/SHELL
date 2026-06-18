"""RagDocument — aggregate root for an indexed document and its chunks."""

from shell.domain.entities.rag_document.rag_chunk import RagChunk
from shell.domain.entities.rag_document.rag_document import RagDocument

__all__ = [
    "RagChunk",
    "RagDocument",
]
