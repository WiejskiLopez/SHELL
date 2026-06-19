"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell.infrastructure.persistence.memory import (
    FakeClock,
    FakeIdGenerator,
)
from shell.infrastructure.persistence.sql.services import RagQueryService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestSqlRagDocumentRepository:
    async def test_index_and_search_similar(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell.application.command_handlers.index_document_handler import (
            IndexDocumentHandler,
        )
        from shell.application.commands.commands import IndexDocumentCommand
        from shell.application.queries.queries import SearchSimilarQuery
        from shell.application.query_handlers.query_handlers import SearchSimilarHandler
        from shell.infrastructure.external.hash_embedder import HashEmbedder

        embedder = HashEmbedder(dim=64)
        text = "SQLite RAG integration test " * 30
        cmd = IndexDocumentCommand(
            source_uri="file:///sql_rag.md", title="SQL RAG", domain="sql-test", text=text
        )
        await IndexDocumentHandler(uow, clock, id_gen, embedder).handle(cmd)

        results = await SearchSimilarHandler(RagQueryService(session_factory), embedder).handle(
            SearchSimilarQuery(query_text="SQLite RAG integration", top_k=5, domain="sql-test")
        )
        assert len(results) > 0
        assert all(r.domain == "sql-test" for r in results)

    async def test_search_domain_filter_excludes_other_domains(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell.application.command_handlers.index_document_handler import (
            IndexDocumentHandler,
        )
        from shell.application.commands.commands import IndexDocumentCommand
        from shell.application.queries.queries import SearchSimilarQuery
        from shell.application.query_handlers.query_handlers import SearchSimilarHandler
        from shell.infrastructure.external.hash_embedder import HashEmbedder

        embedder = HashEmbedder(dim=64)
        await IndexDocumentHandler(uow, clock, id_gen, embedder).handle(
            IndexDocumentCommand(
                source_uri="file:///x.md", title="X", domain="domain-x", text="unique text x " * 20
            )
        )
        results = await SearchSimilarHandler(RagQueryService(session_factory), embedder).handle(
            SearchSimilarQuery(query_text="unique text x", top_k=5, domain="domain-y")
        )
        assert results == []
