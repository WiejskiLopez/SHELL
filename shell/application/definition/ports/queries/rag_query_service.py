from __future__ import annotations

from typing import Protocol

from shell.application.platform.dto import RagChunkDto


class RagQueryService(Protocol):
    """Port do wyszukiwania semantycznego (RAG)."""

    async def search_similar(
        self, query_embedding: bytes, top_k: int = 5, domain: str | None = None
    ) -> list[RagChunkDto]: ...
