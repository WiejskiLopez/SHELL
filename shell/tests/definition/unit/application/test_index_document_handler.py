"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

from shell.application.definition.command_handlers.index_document_handler import (
    IndexDocumentHandler,
)
from shell.application.platform.commands.commands import IndexDocumentCommand
from shell.application.platform.queries.queries import SearchSimilarQuery
from shell.application.platform.query_handlers.query_handlers import SearchSimilarHandler
from shell.infrastructure.platform.external.hash_embedder import HashEmbedder
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,  # noqa: TC002 — FakeClock używany w sygnaturach fixture'ów pytest
    FakeIdGenerator,  # noqa: TC002 — FakeIdGenerator używany w sygnaturach fixture'ów pytest
    InMemoryQueryServices,  # noqa: TC002 — InMemoryQueryServices używany w sygnaturach fixture'ów pytest
    InMemoryUnitOfWork,  # noqa: TC002 — InMemoryUnitOfWork używany w sygnaturach fixture'ów pytest
)


class TestIndexDocumentHandler:
    async def test_index_and_search_returns_chunks(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        queries: InMemoryQueryServices,
    ) -> None:
        embedder = HashEmbedder(dim=64)
        cmd = IndexDocumentCommand(
            source_uri="file:///doc.md",
            title="Doc",
            domain="test",
            text="Hello world " * 50,
        )
        doc_id = await IndexDocumentHandler(uow, clock, id_gen, embedder).handle(cmd)
        assert doc_id is not None

        results = await SearchSimilarHandler(queries, embedder).handle(
            SearchSimilarQuery(query_text="Hello world", top_k=3, domain="test")
        )
        assert len(results) > 0
        assert results[0].domain == "test"

    async def test_index_empty_text_creates_no_chunks(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        embedder = HashEmbedder(dim=64)
        cmd = IndexDocumentCommand(
            source_uri="file:///empty.md", title="Empty", domain="x", text=""
        )
        doc_id = await IndexDocumentHandler(uow, clock, id_gen, embedder).handle(cmd)
        assert doc_id is not None
        doc = await uow.rag_documents.get_by_id(doc_id)
        assert doc is not None
        assert list(doc.chunks) == []
