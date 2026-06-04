"""SqlAlchemyUnitOfWork \u2014 transactional boundary for SQL backends."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shell_ddd.domain.entities.envelope import Envelope
from shell_ddd.infrastructure.persistence.sql.repositories import (
    SqlEnvelopeArchiveStub,
    SqlEnvelopeRepository,
    SqlNodeResultRepository,
    SqlPromptRepository,
    SqlRagDocumentRepository,
    SqlRunnerConfigRepository,
    SqlSessionRepository,
    SqlTaskRepository,
    SqlWorkflowRepository,
)


class SqlAlchemyUnitOfWork:
    """UnitOfWork backed by SQLAlchemy AsyncSession.

    Works for both SQLite (sqlite+aiosqlite) and PostgreSQL (postgresql+asyncpg).
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = session_factory

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self._session: AsyncSession = self._factory()
        self.tasks = SqlTaskRepository(self._session)
        self.workflows = SqlWorkflowRepository(self._session)
        self.envelopes = SqlEnvelopeRepository(self._session)
        self.prompts = SqlPromptRepository(self._session)
        self.node_results = SqlNodeResultRepository(self._session)
        self.runner_configs = SqlRunnerConfigRepository(self._session)
        self.envelope_archive: SqlEnvelopeArchiveStub = SqlEnvelopeArchiveStub()
        self.rag_documents = SqlRagDocumentRepository(self._session)
        self.sessions = SqlSessionRepository(self._session)
        return self

    async def __aexit__(self, exc_type: object, *args: object) -> None:
        if exc_type:
            await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
