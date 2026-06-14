"""SqlAlchemyUnitOfWork \u2014 transactional boundary for SQL backends."""
from __future__ import annotations

import dataclasses
import uuid
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shell_ddd.infrastructure.persistence.sql.models import OutboxEventModel
from shell_ddd.infrastructure.persistence.sql.repositories import (
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
    from shell_ddd.application.ports.messaging import EventPublisher
    from shell_ddd.domain.events.events import DomainEvent


class SqlAlchemyUnitOfWork:
    """UnitOfWork backed by SQLAlchemy AsyncSession.

    Works for both SQLite (sqlite+aiosqlite) and PostgreSQL (postgresql+asyncpg).
    Outbox events are written to the same session — atomically with domain state.

    After a successful commit, ``__aexit__`` dispatches the staged events to the
    optional ``post_commit_publisher`` (logger, audit, in-process EventBus). The
    outbox row written inside ``commit()`` is the durable source of truth — the
    post-commit publisher is best-effort fan-out for side effects only.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        post_commit_publisher: EventPublisher | None = None,
    ) -> None:
        self._factory = session_factory
        self._post_commit_publisher = post_commit_publisher
        self._staged_events: list[DomainEvent] = []
        self._post_commit_buffer: list[DomainEvent] = []
        self._committed = False

    # ------------------------------------------------------------------
    # Outbox staging — handlers call uow.stage_events() BEFORE commit
    # ------------------------------------------------------------------

    def stage_events(self, events: list[DomainEvent]) -> None:
        """Accumulate domain events to be written to the outbox inside commit()."""
        self._staged_events.extend(events)

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._staged_events)

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self._session: AsyncSession = self._factory()
        self._staged_events = []
        self._post_commit_buffer = []
        self._committed = False
        self.tasks = SqlTaskRepository(self._session)
        self.graphs = SqlGraphRepository(self._session)
        self.workflows = SqlWorkflowRepository(self._session)
        self.envelopes = SqlEnvelopeRepository(self._session)
        self.prompts = SqlPromptRepository(self._session)
        self.runner_configs = SqlRunnerConfigRepository(self._session)
        self.envelope_archive: SqlEnvelopeArchiveStub = SqlEnvelopeArchiveStub()
        self.rag_documents = SqlRagDocumentRepository(self._session)
        self.sessions = SqlSessionRepository(self._session)
        self.template_graphs = SqlTemplateGraphRepository(self._session)
        return self

    async def __aexit__(self, exc_type: object, *args: object) -> None:
        try:
            if exc_type:
                await self.rollback()
        finally:
            await self._session.close()
        # Best-effort post-commit fan-out. Outbox row is the durable source of
        # truth and was already written in the same transaction as domain state.
        if exc_type is None and self._committed and self._post_commit_publisher is not None:
            buffered = self._post_commit_buffer
            self._post_commit_buffer = []
            await self._post_commit_publisher.publish(buffered)

    async def commit(self) -> None:
        """Write staged outbox events to DB and commit everything in one transaction."""
        for event in self._staged_events:
            payload = {
                f.name: str(getattr(event, f.name))
                for f in dataclasses.fields(event)  # type: ignore[arg-type]
                if f.name != "occurred_at"
            }
            self._session.add(
                OutboxEventModel(
                    id=str(uuid.uuid4()),
                    event_type=type(event).__name__,
                    occurred_at=event.occurred_at,
                    payload=payload,
                    published_at=None,
                )
            )
        self._post_commit_buffer = list(self._staged_events)
        self._staged_events = []
        await self._session.commit()
        self._committed = True

    async def rollback(self) -> None:
        self._staged_events = []
        self._post_commit_buffer = []
        self._committed = False
        await self._session.rollback()
