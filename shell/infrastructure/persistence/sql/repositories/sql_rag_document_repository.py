from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import delete as sa_delete
from sqlalchemy.orm import selectinload

from shell.domain.repositories.rag_repository import RagDocumentRepository
from shell.domain.value_objects.ids import RagDocumentId

from ..mappers import (
    rag_chunk_entity_to_model,
    rag_document_entity_to_model,
    rag_document_model_to_entity,
)
from ..models import RagChunkModel, RagDocumentModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.entities.rag_document import RagChunk, RagDocument
    from shell.infrastructure.persistence.sql.rag_search import RagSearchStrategy

logger = logging.getLogger(__name__)


class SqlRagDocumentRepository(RagDocumentRepository):
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
        doc_model = rag_document_entity_to_model(document)
        await self._session.merge(doc_model)
        await self._session.execute(
            sa_delete(RagChunkModel).where(RagChunkModel.document_id == document.id.value)
        )
        for chunk in document.chunks:
            self._session.add(rag_chunk_entity_to_model(chunk))

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
        return rag_document_model_to_entity(row)

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
