from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from shell.domain.definition.repositories.rag_repository import RagDocumentRepository
from shell.domain.definition.value_objects.ids import (
    RagDocumentId,  # noqa: TC002 — RagDocumentId używany w konstruktorach w repozytorium
)
from shell.infrastructure.definition.persistence.sql.mappers import (
    rag_chunk_entity_to_model,
    rag_document_entity_to_model,
    rag_document_model_to_entity,
    rag_document_update_model,
)
from sqlalchemy import delete as sa_delete
from sqlalchemy.orm import selectinload

from ..models import RagChunkModel, RagDocumentModel

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.rag_document import RagChunk, RagDocument
    from shell.infrastructure.platform.persistence.sql.rag_search import RagSearchStrategy
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SqlRagDocumentRepository(RagDocumentRepository):
    def __init__(
        self,
        session: AsyncSession,
        search_strategy: RagSearchStrategy | None = None,
    ) -> None:
        self._session = session
        self._search_strategy = search_strategy

    def _get_strategy(self) -> RagSearchStrategy:
        if self._search_strategy is None:
            from shell.infrastructure.platform.persistence.sql.rag_search import (
                InMemoryRagSearchStrategy,
            )

            self._search_strategy = InMemoryRagSearchStrategy()
        return self._search_strategy

    async def save(self, document: RagDocument) -> None:
        doc_model = await self._session.get(RagDocumentModel, document.id.value)
        if doc_model is None:
            doc_model = rag_document_entity_to_model(document)
            self._session.add(doc_model)
        else:
            rag_document_update_model(doc_model, document)
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


__all__ = [
    "RagChunkModel",
    "RagDocumentModel",
    "SqlRagDocumentRepository",
    "logger",
    "sa_delete",
]
