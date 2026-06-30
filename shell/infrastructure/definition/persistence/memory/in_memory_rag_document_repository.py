from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.rag_document import RagChunk, RagDocument
from shell.domain.definition.repositories.rag_repository import RagDocumentRepository
from shell.domain.definition.value_objects.ids import (
    RagDocumentId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.definition.value_objects.chunk_index import ChunkIndex
    from shell.domain.definition.value_objects.domain_tag import DomainTag
    from shell.domain.definition.value_objects.embedding import Embedding


class InMemoryRagDocumentRepository(
    InMemoryRepository[RagDocument, RagDocumentId], RagDocumentRepository
):
    async def search_similar(
        self,
        query_embedding: Embedding,
        top_k: ChunkIndex,
        domain: DomainTag | None = None,
    ) -> list[RagChunk]:
        import struct

        from shell.domain.definition.services.rag_index_service import cosine_similarity

        query_bytes = query_embedding.value
        dim = len(query_bytes) // 4
        query_vec = list(struct.unpack(f"{dim}f", query_bytes))
        scored: list[tuple[float, RagChunk]] = []
        for doc in self._store.values():
            domain_str = str(domain) if domain else None
            if domain_str and doc.domain.value != domain_str:
                continue
            for chunk in doc.chunks:
                chunk_vec = list(
                    struct.unpack(f"{len(chunk.embedding.value) // 4}f", chunk.embedding.value)
                )
                score = cosine_similarity(query_vec, chunk_vec)
                scored.append((score, chunk))
        scored.sort(key=lambda tuple_item: tuple_item[0], reverse=True)
        return [chunk for _, chunk in scored[: top_k.value]]
