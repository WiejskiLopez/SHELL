from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from shell.application.definition.dto.rag_chunk import RagChunkDto
from shell.infrastructure.definition.persistence.sql.models import RagChunkModel, RagDocumentModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class RagQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def search_similar(
        self, query_embedding: bytes, top_k: int = 5, domain: str | None = None
    ) -> list[RagChunkDto]:
        async with self._session_factory() as session:
            stmt = select(RagChunkModel).options(joinedload(RagChunkModel.document))
            if domain:
                stmt = stmt.join(RagChunkModel.document).where(RagDocumentModel.domain == domain)
            res = await session.execute(stmt.limit(100))
            return [
                RagChunkDto(
                    chunk_id=str(rag_chunk_model.id),
                    document_id=str(rag_chunk_model.document_id),
                    chunk_index=rag_chunk_model.chunk_index,
                    chunk_text=rag_chunk_model.chunk_text,
                    source_uri=rag_chunk_model.document.source_uri,
                    title=rag_chunk_model.document.title,
                    domain=rag_chunk_model.document.domain,
                    score=0.0,
                )
                for rag_chunk_model in res.scalars()
            ][:top_k]


__all__ = [
    "RagQueryService",
    "joinedload",
]
