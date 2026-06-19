from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import delete as sa_delete
from sqlalchemy.orm import selectinload

from shell.domain.entities.rag_document import RagChunk, RagDocument
from shell.domain.value_objects.ids import RagChunkId, RagDocumentId

from ..models import RagChunkModel, RagDocumentModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.infrastructure.persistence.sql.rag_search import RagSearchStrategy

logger = logging.getLogger(__name__)


class SqlRagDocumentRepository:
    def __init__(
        self,
        session: AsyncSession,
        search_strategy: RagSearchStrategy | None = None,
    ) -> None:
        self._session = session
        self._search_strategy = search_strategy

    def _get_strategy(self) -> RagSearchStrategy:  # type: ignore[return]
        if self._search_strategy is None:
            from shell.infrastructure.persistence.sql.rag_search import (
                InMemoryRagSearchStrategy,
            )

            self._search_strategy = InMemoryRagSearchStrategy()
        return self._search_strategy  # type: ignore[return]

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
        from sqlalchemy import select

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
        strategy = self._get_strategy()
        return await strategy.search_similar(
            session=self._session,
            query_embedding=query_embedding,
            top_k=top_k,
            domain=domain,
        )
