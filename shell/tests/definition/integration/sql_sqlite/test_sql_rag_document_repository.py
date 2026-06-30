"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.definition.persistence.sql.services import RagQueryService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.infrastructure.platform.persistence import (
        SqlAlchemyUnitOfWork,  # noqa: TC002 — SqlAlchemyUnitOfWork używany w sygnaturach fixture'ów pytest
    )
    from shell.infrastructure.platform.persistence.memory import (  # noqa: TC002 — FakeClock, FakeIdGenerator używane w sygnaturach fixture'ów pytest
        FakeClock,
        FakeIdGenerator,
    )


class TestSqlRagDocumentRepository:
    async def test_index_and_search_similar(
        self,
        sql_uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell.application.definition.command_handlers.document_index_handler import (
            DocumentIndexHandler as IndexDocumentHandler,
        )
        from shell.application.definition.commands.rag_commands import IndexDocumentCommand
        from shell.application.definition.queries.search_similar_query import SearchSimilarQuery
        from shell.application.definition.query_handlers.search_similar_handler import (
            SearchSimilarHandler,
        )
        from shell.infrastructure.platform.external.hash_embedder import HashEmbedder

        embedder = HashEmbedder(dim=64)
        text = "SQLite RAG integration test " * 30
        cmd = IndexDocumentCommand(
            source_uri="file:///sql_rag.md", title="SQL RAG", domain="sql-test", text=text
        )
        await IndexDocumentHandler(sql_uow, clock, id_generator, embedder).handle(cmd)

        results = await SearchSimilarHandler(RagQueryService(session_factory), embedder).handle(
            SearchSimilarQuery(query_text="SQLite RAG integration", top_k=5, domain="sql-test")
        )
        assert len(results) > 0
        assert all(r.domain == "sql-test" for r in results)

    async def test_search_domain_filter_excludes_other_domains(
        self,
        sql_uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell.application.definition.command_handlers.document_index_handler import (
            DocumentIndexHandler as IndexDocumentHandler,
        )
        from shell.application.definition.commands.rag_commands import IndexDocumentCommand
        from shell.application.definition.queries.search_similar_query import SearchSimilarQuery
        from shell.application.definition.query_handlers.search_similar_handler import (
            SearchSimilarHandler,
        )
        from shell.infrastructure.platform.external.hash_embedder import HashEmbedder

        embedder = HashEmbedder(dim=64)
        await IndexDocumentHandler(sql_uow, clock, id_generator, embedder).handle(
            IndexDocumentCommand(
                source_uri="file:///x.md", title="X", domain="domain-x", text="unique text x " * 20
            )
        )
        results = await SearchSimilarHandler(RagQueryService(session_factory), embedder).handle(
            SearchSimilarQuery(query_text="unique text x", top_k=5, domain="domain-y")
        )
        assert results == []
