from __future__ import annotations

import logging
import struct
from typing import TYPE_CHECKING, Protocol

from shell.domain.definition.services.rag_index_service import cosine_similarity
from shell.infrastructure.definition.persistence.sql.models import RagChunkModel, RagDocumentModel
from shell.infrastructure.platform.persistence.sql.mappers import rag_chunk_model_to_entity
from sqlalchemy import select
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.rag_document import RagChunk
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


class RagSearchStrategy(Protocol):
    async def search_similar(
        self,
        session: AsyncSession,
        query_embedding: bytes,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[RagChunk]: ...


class InMemoryRagSearchStrategy:
    def __init__(self) -> None:
        logger.info("Using in-memory (Python) RAG search strategy")

    async def search_similar(
        self,
        session: AsyncSession,
        query_embedding: bytes,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[RagChunk]:
        query = select(RagChunkModel).options(selectinload(RagChunkModel.document))
        if domain:
            query = query.join(RagDocumentModel).where(RagDocumentModel.domain == domain)
        rows = (await session.execute(query)).scalars().all()
        if not rows:
            return []
        dim = len(query_embedding) // 4
        query_vec = list(struct.unpack(f"{dim}f", query_embedding))
        scored: list[tuple[float, RagChunkModel]] = []
        for rag_chunk_model in rows:
            chunk_vec = list(
                struct.unpack(
                    f"{len(rag_chunk_model.embedding) // 4}f",
                    rag_chunk_model.embedding,
                )
            )
            score = cosine_similarity(query_vec, chunk_vec)
            scored.append((score, rag_chunk_model))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [rag_chunk_model_to_entity(rag_chunk_model) for _, rag_chunk_model in scored[:top_k]]


class PgVectorRagSearchStrategy:
    def __init__(self) -> None:
        logger.info("Using pgvector RAG search strategy")

    async def search_similar(
        self,
        session: AsyncSession,
        query_embedding: bytes,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[RagChunk]:
        dim = len(query_embedding) // 4
        query_vec = list(struct.unpack(f"{dim}f", query_embedding))
        from sqlalchemy import text

        vector_literal = "[" + ",".join(str(v) for v in query_vec) + "]"
        stmt = text(
            """
            SELECT rc.id, rc.document_id, rc.chunk_index, rc.chunk_text,
                   rc.embedding, rc.embedding_model
            FROM rag_chunk rc
            JOIN rag_document rd ON rd.id = rc.document_id
            WHERE (:domain IS NULL OR rd.domain = :domain)
            ORDER BY rc.embedding_vector <=> :query_vec::vector
            LIMIT :top_k
            """
        )
        rows = (
            (
                await session.execute(
                    stmt,
                    {
                        "query_vec": vector_literal,
                        "domain": domain,
                        "top_k": top_k,
                    },
                )
            )
            .mappings()
            .all()
        )
        return [
            rag_chunk_model_to_entity(
                RagChunkModel(
                    id=row["id"],
                    document_id=row["document_id"],
                    chunk_index=row["chunk_index"],
                    chunk_text=row["chunk_text"],
                    embedding=row["embedding"],
                    embedding_model=row["embedding_model"],
                )
            )
            for row in rows
        ]


def create_rag_search_strategy(session_factory: async_sessionmaker[AsyncSession]) -> RagSearchStrategy:
    engine = getattr(session_factory, "bind", None)
    dialect_name: str = engine.dialect.name if engine is not None else "unknown"
    if dialect_name == "postgresql":
        try:
            return PgVectorRagSearchStrategy()
        except ImportError:
            logger.warning("pgvector not available, falling back to in-memory search")
            return InMemoryRagSearchStrategy()
    return InMemoryRagSearchStrategy()
