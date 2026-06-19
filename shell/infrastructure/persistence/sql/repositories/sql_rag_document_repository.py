from __future__ import annotations

import logging
import struct
from typing import TYPE_CHECKING

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.orm import selectinload

from shell.domain.entities.rag_document import RagChunk, RagDocument
from shell.domain.services.rag_index_service import cosine_similarity
from shell.domain.value_objects.ids import RagChunkId, RagDocumentId

from ..models import RagChunkModel, RagDocumentModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SqlRagDocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, document: RagDocument) -> None:
        doc_model = RagDocumentModel(
            id=document.id.value,
            source_uri=document.source_uri,
            title=document.title,
            domain=document.domain,
            created_at=document.created_at,
        )
        await self._session.merge(doc_model)
        await self._session.execute(
            sa_delete(RagChunkModel).where(RagChunkModel.document_id == document.id.value)
        )
        for chunk in document.chunks:
            self._session.add(
                RagChunkModel(
                    id=chunk.id.value,
                    document_id=chunk.document_id.value,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    embedding=chunk.embedding,
                    embedding_model=chunk.embedding_model,
                )
            )

    async def get_by_id(self, doc_id: RagDocumentId) -> RagDocument | None:
        query = (
            select(RagDocumentModel)
            .options(selectinload(RagDocumentModel.chunks))
            .where(RagDocumentModel.id == doc_id.value)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        if row is None:
            return None
        doc = RagDocument(
            id=RagDocumentId(row.id),
            source_uri=row.source_uri,
            title=row.title,
            domain=row.domain,
            created_at=row.created_at,
        )
        for chunk in sorted(row.chunks, key=lambda chunk_entry: chunk_entry.chunk_index):
            doc.chunks.append(
                RagChunk(
                    id=RagChunkId(chunk.id),
                    document_id=RagDocumentId(chunk.document_id),
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    embedding=chunk.embedding,
                    embedding_model=chunk.embedding_model,
                )
            )
        return doc

    async def search_similar(
        self,
        query_embedding: bytes,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[RagChunk]:
        query = select(RagChunkModel).options(selectinload(RagChunkModel.document))
        if domain:
            query = query.join(RagDocumentModel).where(RagDocumentModel.domain == domain)
        rows = (await self._session.execute(query)).scalars().all()
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
        return [
            RagChunk(
                id=RagChunkId(rag_chunk_model.id),
                document_id=RagDocumentId(rag_chunk_model.document_id),
                chunk_index=rag_chunk_model.chunk_index,
                chunk_text=rag_chunk_model.chunk_text,
                embedding=rag_chunk_model.embedding,
                embedding_model=rag_chunk_model.embedding_model,
            )
            for _, rag_chunk_model in scored[:top_k]
        ]
