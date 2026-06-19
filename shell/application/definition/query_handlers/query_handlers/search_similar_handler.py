from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.platform.dto import RagChunkDto
    from shell.application.platform.ports.queries import RagQueryService
    from shell.application.platform.queries.queries import SearchSimilarQuery
    from shell.domain.definition.services.rag_index_service import Embedder


class SearchSimilarHandler:
    def __init__(self, queries: RagQueryService, embedder: Embedder) -> None:
        self._queries = queries
        self._embedder = embedder

    async def handle(self, query: SearchSimilarQuery) -> list[RagChunkDto]:
        import struct

        vector = self._embedder.embed_text(query.query_text)
        vector_bytes = struct.pack(f"{len(vector)}f", *vector)
        return await self._queries.search_similar(vector_bytes, query.top_k, query.domain)
