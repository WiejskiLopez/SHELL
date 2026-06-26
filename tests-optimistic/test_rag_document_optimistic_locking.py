"""Optimistic locking tests for RagDocument aggregate."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest
from shell.domain.definition.aggregates.rag_document.rag_document import RagDocument
from shell.domain.definition.value_objects.ids import RagDocumentId
from shell.domain.platform.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


_NOW = datetime(2024, 1, 1, 12, 0, 0)


class TestRagDocumentOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        uow1 = SqlAlchemyUnitOfWork(session_factory)
        uow2 = SqlAlchemyUnitOfWork(session_factory)
        doc_id = RagDocumentId.generate()

        async with uow1 as u:
            doc = RagDocument.new(
                id_=doc_id,
                source_uri="https://example.com/doc",
                title="Test",
                domain="test",
                now=_NOW,
            )
            await u.rag_document_repository.save(doc)
            await u.commit()

        async with uow1 as u1:
            entity_a = await u1.rag_document_repository.get_by_id(doc_id)
            assert entity_a is not None

            async with uow2 as u2:
                entity_b = await u2.rag_document_repository.get_by_id(doc_id)
                assert entity_b is not None

                modified_a = RagDocument(
                    id=doc_id,
                    source_uri="https://example.com/doc-v2",
                    title="Test V2",
                    domain="test",
                    created_at=_NOW,
                )
                await u1.rag_document_repository.save(modified_a)
                await u1.commit()

                modified_b = RagDocument(
                    id=doc_id,
                    source_uri="https://example.com/doc-v3",
                    title="Test V3",
                    domain="test",
                    created_at=_NOW,
                )
                await u2.rag_document_repository.save(modified_b)
                with pytest.raises(ConcurrentModificationError):
                    await u2.commit()
