from __future__ import annotations

import struct
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.definition.dto.rag_chunk import RagChunkDto
    from shell.application.definition.queries.rag_search_similar_query import RagSearchSimilarQuery
    from shell.application.platform.ports.queries import RagQueryService
    from shell.domain.definition.services.rag_index_service import Embedder


class RagSearchSimilarHandler:
    def __init__(self, queries: RagQueryService, embedder: Embedder) -> None:
        self._queries = queries
        self._embedder = embedder

    async def handle(self, query: RagSearchSimilarQuery) -> list[RagChunkDto]:
        vector = self._embedder.embed_text(query.query_text)
        vector_bytes = struct.pack(f"{len(vector)}f", *vector)
        return await self._queries.search_similar(
            vector_bytes, query.top_k, query.domain
        )
