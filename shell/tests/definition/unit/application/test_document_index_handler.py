"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.definition.command_handlers.document_index_handler import (
    DocumentIndexHandler,
)
from shell.application.definition.commands.rag_commands import IndexDocumentCommand
from shell.application.definition.queries.rag_search_similar_query import RagSearchSimilarQuery
from shell.application.definition.query_handlers.rag_search_similar_handler import (
    RagSearchSimilarHandler,
)
from shell.domain.definition.value_objects.ids import RagDocumentId
from shell.infrastructure.definition.persistence.memory.in_memory_rag_document_repository import (
    InMemoryRagDocumentRepository,
)
from shell.infrastructure.platform.external.hash_embedder import HashEmbedder

if TYPE_CHECKING:
    from shell.infrastructure.platform.persistence.memory import (
        FakeClock,
        FakeIdGenerator,
        InMemoryQueryServices,
        InMemoryUnitOfWork,
    )


class TestDocumentIndexHandler:
    async def test_index_and_search_returns_chunks(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        queries: InMemoryQueryServices,
    ) -> None:
        embedder = HashEmbedder(dim=64)
        command = IndexDocumentCommand(
            source_uri="file:///doc.md",
            title="Doc",
            domain="test",
            text="Hello world " * 50,
        )
        doc_id = await DocumentIndexHandler(unit_of_work, clock, id_generator, embedder).handle(
            command
        )
        assert doc_id is not None

        results = await RagSearchSimilarHandler(queries, embedder).handle(
            RagSearchSimilarQuery(query_text="Hello world", top_k=3, domain="test")
        )
        assert len(results) > 0
        assert results[0].domain == "test"

    async def test_index_empty_text_creates_no_chunks(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        embedder = HashEmbedder(dim=64)
        command = IndexDocumentCommand(
            source_uri="file:///empty.md", title="Empty", domain="x", text=""
        )
        doc_id = await DocumentIndexHandler(unit_of_work, clock, id_generator, embedder).handle(
            command
        )
        assert doc_id is not None
        doc = await unit_of_work.repository(InMemoryRagDocumentRepository).get_by_id(RagDocumentId(doc_id))
        assert doc is not None
        assert list(doc.chunks) == []
