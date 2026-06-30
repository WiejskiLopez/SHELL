from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.rag_document import RagChunk, RagDocument
    from shell.domain.definition.value_objects.chunk_index import ChunkIndex
    from shell.domain.definition.value_objects.domain_tag import DomainTag
    from shell.domain.definition.value_objects.embedding import Embedding
    from shell.domain.definition.value_objects.ids import RagDocumentId
    from shell.domain.platform.value_objects.exists_result import ExistsResult


class RagDocumentRepository(Protocol):
    async def save(self, document: RagDocument) -> None: ...
    async def get_by_id(self, doc_id: RagDocumentId) -> RagDocument | None: ...
    async def search_similar(
        self,
        query_embedding: Embedding,
        top_k: ChunkIndex,
        domain: DomainTag | None = None,
    ) -> list[RagChunk]: ...
    async def delete(self, id: RagDocumentId) -> None: ...
    async def exists(self, id: RagDocumentId) -> ExistsResult: ...
