from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.definition.rag_document.dto.rag_chunk import RagChunkDto
    from shell.application.definition.rag_document.ports.rag_query_service import RagQueryService
    from shell.application.definition.rag_document.queries.rag_document_get_by_id_query import (
        RagDocumentGetByIdQuery,
    )


class RagDocumentGetByIdHandler:
    def __init__(self, queries: RagQueryService) -> None:
        self._queries = queries

    async def handle(self, query: RagDocumentGetByIdQuery) -> RagChunkDto | None:
        return await self._queries.get_by_id(query.document_id)
