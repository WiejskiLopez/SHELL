from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.repositories.rag_repository import RagDocumentRepository
from shell.domain.definition.value_objects.ids import RagDocumentId

if TYPE_CHECKING:
    from shell.domain.definition.entities.rag_document import RagChunk, RagDocument


class InMemoryRagDocumentRepository(RagDocumentRepository):
    def __init__(self) -> None:
        self._store: dict[str, RagDocument] = {}

    async def save(self, document: RagDocument) -> None:
        self._store[document.id.value] = document

    async def get_by_id(self, doc_id: RagDocumentId) -> RagDocument | None:
        return self._store.get(doc_id.value)

    async def search_similar(
        self,
        query_embedding: bytes,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[RagChunk]:
        import struct

        from shell.domain.definition.services.rag_index_service import cosine_similarity

        dim = len(query_embedding) // 4
        query_vec = list(struct.unpack(f"{dim}f", query_embedding))
        scored: list[tuple[float, RagChunk]] = []
        for doc in self._store.values():
            if domain and doc.domain != domain:
                continue
            for chunk in doc.chunks:
                chunk_vec = list(struct.unpack(f"{len(chunk.embedding) // 4}f", chunk.embedding))
                score = cosine_similarity(query_vec, chunk_vec)
                scored.append((score, chunk))
        scored.sort(key=lambda tuple_item: tuple_item[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]
