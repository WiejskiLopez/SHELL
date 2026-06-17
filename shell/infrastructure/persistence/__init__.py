"""SqlAlchemyUnitOfWork — transactional boundary for SQL backends."""

from __future__ import annotations

import dataclasses
import uuid
from typing import TYPE_CHECKING

from shell.application.ports.unit_of_work import UnitOfWork
from shell.infrastructure.persistence.sql.models import OutboxEventModel
from shell.infrastructure.persistence.sql.repositories import (
    SqlEnvelopeArchiveStub,
    SqlEnvelopeRepository,
    SqlGraphRepository,
    SqlPromptRepository,
    SqlRagDocumentRepository,
    SqlRunnerConfigRepository,
    SqlSessionRepository,
    SqlTaskRepository,
    SqlTemplateGraphRepository,
    SqlWorkflowRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.domain.events.events import DomainEvent


class SqlAlchemyUnitOfWork(UnitOfWork):
    """UnitOfWork backed by SQLAlchemy AsyncSession.

    Works for both SQLite (sqlite+aiosqlite) and PostgreSQL (postgresql+asyncpg).
    Outbox events are written to the same session — atomically with domain state.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._factory = session_factory
        self._staged_events: list[DomainEvent] = []
        self._committed = False
        self._session: AsyncSession | None = None

    # ------------------------------------------------------------------
    # Internal state guards
    # ------------------------------------------------------------------

    @property
    def _active_session(self) -> AsyncSession:
        """Zwraca aktywną sesję lub rzuca błąd, jeśli UoW nie zostało otwarte."""
        if self._session is None:
            raise RuntimeError("UnitOfWork not entered; use 'async with'")
        return self._session

    # ------------------------------------------------------------------
    # Repository properties (covariant return types — mypy-friendly)
    # ------------------------------------------------------------------

    # Tworzenie obiektów w locie jest tutaj w pełni bezpieczne i optymalne,
    # o ile Twoje repozytoria SQLAlchemy są bezstanowymi fasadami na sesję.

    @property
    def tasks(self) -> SqlTaskRepository:
        return SqlTaskRepository(self._active_session)

    @property
    def graphs(self) -> SqlGraphRepository:
        return SqlGraphRepository(self._active_session)

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
        return SqlRagDocumentRepository(self._active_session)

    @property
    def sessions(self) -> SqlSessionRepository:
        return SqlSessionRepository(self._active_session)

    @property
    def template_graphs(self) -> SqlTemplateGraphRepository:
        return SqlTemplateGraphRepository(self._active_session)

    # ------------------------------------------------------------------
    # Outbox staging — handlers call uow.stage_events() BEFORE commit
    # ------------------------------------------------------------------

    def stage_events(self, events: list[DomainEvent]) -> None:
        """Accumulate domain events to be written to the outbox inside commit()."""
        self._staged_events.extend(events)

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._staged_events)

    # ------------------------------------------------------------------
    # Context Management & Transaction Control
    # ------------------------------------------------------------------

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._factory()
        self._staged_events = []
        self._committed = False
        return self

    async def __aexit__(self, exc_type: object, *args: object) -> None:
        try:
            if exc_type:
                await self.rollback()
        finally:
            if self._session:
                await self._session.close()
                self._session = None  # Czyszczenie referencji!

    async def commit(self) -> None:
        """Write staged outbox events to DB and commit everything in one transaction."""
        session = self._active_session  # Zabezpieczenie przed typem Optional

        for event in self._staged_events:
            payload = {
                f.name: str(getattr(event, f.name))
                for f in dataclasses.fields(event)
                if f.name != "occurred_at"
            }
            session.add(
                OutboxEventModel(
                    id=str(uuid.uuid4()),
                    event_type=type(event).__name__,
                    occurred_at=event.occurred_at,
                    payload=payload,
                    published_at=None,
                )
            )

        self._staged_events = []
        await session.commit()
        self._committed = True

    async def rollback(self) -> None:
        self._staged_events = []
        self._committed = False
        if self._session:
            await self._session.rollback()
