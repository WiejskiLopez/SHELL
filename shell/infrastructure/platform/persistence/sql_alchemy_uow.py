from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from shell.application.platform.ports.unit_of_work import UnitOfWork
from shell.infrastructure.definition.persistence.sql.repositories import (
    SqlGraphDefinitionRepository,
    SqlPromptRepository,
    SqlRagDocumentRepository,
    SqlRunnerConfigRepository,
)
from shell.infrastructure.execution.persistence.sql.repositories import (
    SqlEnvelopeArchiveStub,
    SqlEnvelopeRepository,
    SqlGraphExecutionRepository,
    SqlSessionRepository,
    SqlTaskExecutionRepository,
    SqlWorkflowRepository,
)
from shell.infrastructure.platform.persistence.sql.models import (
    OutboxEventModel
)
from shell.infrastructure.platform.persistence.sql.rag_search import create_rag_search_strategy
from shell.infrastructure.platform.serialization import DomainEventSerializer

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.domain.platform.events import DomainEvent


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._factory = session_factory
        self._staged_events: list[DomainEvent] = []
        self._committed = False
        self._session: AsyncSession | None = None
        self._rag_search_strategy = create_rag_search_strategy(session_factory)

    @property
    def _active_session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UnitOfWork not entered; use 'async with'")
        return self._session

    @property
    def task_executions(self) -> SqlTaskExecutionRepository:
        return SqlTaskExecutionRepository(self._active_session)

    @property
    def graph_executions(self) -> SqlGraphExecutionRepository:
        return SqlGraphExecutionRepository(self._active_session)

    @property
    def workflows(self) -> SqlWorkflowRepository:
        return SqlWorkflowRepository(self._active_session)

    @property
    def envelopes(self) -> SqlEnvelopeRepository:
        return SqlEnvelopeRepository(self._active_session)

    @property
    def prompts(self) -> SqlPromptRepository:
        return SqlPromptRepository(self._active_session)

    @property
    def runner_configs(self) -> SqlRunnerConfigRepository:
        return SqlRunnerConfigRepository(self._active_session)

    @property
    def envelope_archive(self) -> SqlEnvelopeArchiveStub:
        return SqlEnvelopeArchiveStub()

    @property
    def rag_documents(self) -> SqlRagDocumentRepository:
        return SqlRagDocumentRepository(
            self._active_session,
            search_strategy=self._rag_search_strategy,
        )

    @property
    def sessions(self) -> SqlSessionRepository:
        return SqlSessionRepository(self._active_session)

    @property
    def graph_definitions(self) -> SqlGraphDefinitionRepository:
        return SqlGraphDefinitionRepository(self._active_session)

    def stage_events(self, events: list[DomainEvent]) -> None:
        self._staged_events.extend(events)

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._staged_events)

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._factory()
        self._staged_events = []
        self._committed = False
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        try:
            if exc_type:
                await self.rollback()
            elif not self._committed:
                await self.commit()
        finally:
            if self._session:
                await self._session.close()
                self._session = None

    async def commit(self) -> None:
        session = self._active_session
        serializer = DomainEventSerializer()

        for event in self._staged_events:
            try:
                payload = serializer.to_payload(event)
                session.add(
                    OutboxEventModel(
                        id=str(uuid.uuid4()),
                        event_type=type(event).__name__,
                        occurred_at=event.occurred_at,
                        payload=payload,
                        published_at=None,
                    )
                )
            except Exception:
                import logging

                logging.getLogger(__name__).exception(
                    "Failed to serialize outbox event %s", type(event).__name__
                )
                continue

        self._staged_events = []
        await session.commit()
        self._committed = True

    async def rollback(self) -> None:
        self._staged_events = []
        self._committed = False
        if self._session:
            await self._session.rollback()
