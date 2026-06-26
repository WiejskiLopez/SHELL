from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy.orm.exc import StaleDataError

from shell.application.platform.ports.unit_of_work import UnitOfWork
from shell.domain.platform.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.infrastructure.definition.persistence.sql.repositories import (
    SqlGraphDefinitionRepository,
    SqlRagDocumentRepository,
    SqlRunnerConfigRepository,
)
from shell.infrastructure.execution.persistence.sql.repositories import (
    SqlEnvelopeArchiveStub,
    SqlEnvelopeRepository,
    SqlGraphExecutionRepository,
    SqlGraphExecutionStateInputRepository,
    SqlGraphExecutionStateOutputRepository,
    SqlGraphNodeExecutionRepository,
    SqlGraphNodeExecutionStateRepository,
    SqlGraphNodeTransitionExecutionRepository,
    SqlSessionRepository,
    SqlTaskExecutionRepository,
    SqlTaskExecutionStateInputRepository,
    SqlTaskExecutionStateOutputRepository,
    SqlWorkflowRepository,
)
from shell.infrastructure.platform.persistence.sql.models import OutboxEventModel
from shell.infrastructure.platform.persistence.sql.rag_search import create_rag_search_strategy
from shell.infrastructure.platform.serialization import DomainEventSerializer

if TYPE_CHECKING:
    from shell.domain.platform.events import DomainEvent
    from shell.infrastructure.scheduling.persistence.sql.repositories.sql_scheduler_definition_repository import (
        SqlSchedulerDefinitionRepository,
    )
    from shell.infrastructure.scheduling.persistence.sql.repositories.sql_scheduler_execution_repository import (
        SqlSchedulerExecutionRepository,
    )
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


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
    def task_execution_repository(self) -> SqlTaskExecutionRepository:
        return SqlTaskExecutionRepository(self._active_session)

    @property
    def task_execution_state_repository(self) -> SqlTaskExecutionStateInputRepository:
        return SqlTaskExecutionStateInputRepository(self._active_session)

    @property
    def graph_execution_repository(self) -> SqlGraphExecutionRepository:
        return SqlGraphExecutionRepository(self._active_session)

    @property
    def workflow_repository(self) -> SqlWorkflowRepository:
        return SqlWorkflowRepository(self._active_session)

    @property
    def envelope_repository(self) -> SqlEnvelopeRepository:
        return SqlEnvelopeRepository(self._active_session)

    @property
    def graph_execution_state_repository(self) -> SqlGraphExecutionStateInputRepository:
        return SqlGraphExecutionStateInputRepository(self._active_session)

    @property
    def runner_config_repository(self) -> SqlRunnerConfigRepository:
        return SqlRunnerConfigRepository(self._active_session)

    @property
    def envelope_archive(self) -> SqlEnvelopeArchiveStub:
        return SqlEnvelopeArchiveStub()

    @property
    def rag_document_repository(self) -> SqlRagDocumentRepository:
        return SqlRagDocumentRepository(
            self._active_session,
            search_strategy=self._rag_search_strategy,
        )

    @property
    def graph_definition_repository(self) -> SqlGraphDefinitionRepository:
        return SqlGraphDefinitionRepository(self._active_session)

    @property
    def graph_node_execution_repository(self) -> SqlGraphNodeExecutionRepository:
        return SqlGraphNodeExecutionRepository(self._active_session)

    @property
    def graph_node_execution_state_repository(self) -> SqlGraphNodeExecutionStateRepository:
        return SqlGraphNodeExecutionStateRepository(self._active_session)

    @property
    def graph_node_transition_execution_repository(self) -> SqlGraphNodeTransitionExecutionRepository:
        return SqlGraphNodeTransitionExecutionRepository(self._active_session)

    @property
    def graph_execution_state_input_repository(self) -> SqlGraphExecutionStateInputRepository:
        return SqlGraphExecutionStateInputRepository(self._active_session)

    @property
    def graph_execution_state_output_repository(self) -> SqlGraphExecutionStateOutputRepository:
        return SqlGraphExecutionStateOutputRepository(self._active_session)

    @property
    def task_execution_state_input_repository(self) -> SqlTaskExecutionStateInputRepository:
        return SqlTaskExecutionStateInputRepository(self._active_session)

    @property
    def task_execution_state_output_repository(self) -> SqlTaskExecutionStateOutputRepository:
        return SqlTaskExecutionStateOutputRepository(self._active_session)

    @property
    def session_repository(self) -> SqlSessionRepository:
        return SqlSessionRepository(self._active_session)

    @property
    def scheduler_definition_repository(self) -> SqlSchedulerDefinitionRepository:
        from shell.infrastructure.scheduling.persistence.sql.repositories.sql_scheduler_definition_repository import (
            SqlSchedulerDefinitionRepository,
        )

        return SqlSchedulerDefinitionRepository(self._active_session)

    @property
    def scheduler_execution_repository(self) -> SqlSchedulerExecutionRepository:
        from shell.infrastructure.scheduling.persistence.sql.repositories.sql_scheduler_execution_repository import (
            SqlSchedulerExecutionRepository,
        )

        return SqlSchedulerExecutionRepository(self._active_session)

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._factory()
        await self._session.__aenter__()
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._session is not None:
            await self._session.__aexit__(*args)
            self._session = None

    async def commit(self) -> None:
        if self._session is None:
            return
        try:
            for event in self._staged_events:
                outbox = OutboxEventModel(
                    id=str(uuid.uuid4()),
                    event_type=type(event).__name__,
                    aggregate_id=event.aggregate_id,
                    aggregate_type=event.aggregate_type,
                    data=DomainEventSerializer.serialize(event),
                    occurred_at=event.occurred_at,
                )
                self._session.add(outbox)
            await self._session.commit()
            self._staged_events.clear()
            self._committed = True
        except StaleDataError as exc:
            await self._session.rollback()
            raise ConcurrentModificationError("Aggregate", str(exc)) from exc

    async def rollback(self) -> None:
        if self._session is not None:
            await self._session.rollback()
        self._staged_events.clear()

    def stage_events(self, events: list[DomainEvent]) -> None:
        self._staged_events.extend(events)
