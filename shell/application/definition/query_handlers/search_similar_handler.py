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

    async def handle(self, search_similar_query: SearchSimilarQuery) -> list[RagChunkDto]:
        import struct

        vector = self._embedder.embed_text(search_similar_query.query_text)
        vector_bytes = struct.pack(f"{len(vector)}f", *vector)
        return await self._queries.search_similar(vector_bytes, search_similar_query.top_k, search_similar_query.domain)
