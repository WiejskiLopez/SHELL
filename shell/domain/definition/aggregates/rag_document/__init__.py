"""RagDocument — aggregate root for an indexed document and its chunks."""

from __future__ import annotations

from shell.domain.definition.aggregates.rag_document.entities.rag_chunk import RagChunk
from shell.domain.definition.aggregates.rag_document.rag_document import RagDocument

__all__ = [
    "RagChunk",
    "RagDocument",
]
