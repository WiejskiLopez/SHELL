from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.rag_document import RagChunk, RagDocument
    from shell.domain.definition.value_objects.ids import RagDocumentId


# TODO: add delete()\n# TODO: add exists()\nclass RagDocumentRepository(Protocol):
    async def save(self, document: RagDocument) -> None: ...
    async def get_by_id(self, doc_id: RagDocumentId) -> RagDocument | None: ...
    async def search_similar(
        self,
        query_embedding: bytes,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[RagChunk]: ...
async def delete(self, id: RagDocumentId) -> None: ...
async def exists(self, id: RagDocumentId) -> bool: ...
