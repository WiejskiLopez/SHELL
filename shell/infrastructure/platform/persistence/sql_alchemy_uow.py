from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, TypeVar

from sqlalchemy.orm.exc import StaleDataError

from shell.application.platform.ports.unit_of_work import UnitOfWork
from shell.domain.definition.aggregates.graph_definition_embedding.repositories.graph_definition_embedding_repository import (
    GraphDefinitionEmbeddingRepository,
)
from shell.domain.definition.aggregates.graph_node_transition_definition.repositories.graph_node_transition_definition_repository import (
    GraphNodeTransitionDefinitionRepository,
)
from shell.domain.definition.repositories.graph_definition_repository.graph_definition_repository import (
    GraphDefinitionRepository,
)
from shell.domain.definition.repositories.graph_definition_repository.graph_node_definition_repository import (
    GraphNodeDefinitionRepository,
)
from shell.domain.definition.repositories.rag_repository import RagDocumentRepository
from shell.domain.definition.repositories.runner_config_repository import RunnerConfigRepository
from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.graph_execution_state.repositories.graph_execution_state_repository import (
    GraphExecutionStateRepository,
)
from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.aggregates.graph_node_execution_state.repositories.graph_node_execution_state_repository import (
    GraphNodeExecutionStateRepository,
)
from shell.domain.execution.aggregates.graph_node_transition_execution.repositories.graph_node_transition_execution_repository import (
    GraphNodeTransitionExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution_state.repositories.task_execution_state_repository import (
    TaskExecutionStateRepository,
)
from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.aggregates.workflow_state.repositories.workflow_state_repository import (
    WorkflowStateRepository,
)
from shell.domain.platform.aggregates.message.repositories.message_repository import (
    MessageRepository,
)
from shell.domain.platform.envelope import Envelope
from shell.domain.platform.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.infrastructure.definition.persistence.sql.repositories import (
    SqlGraphDefinitionEmbeddingRepository,
    SqlGraphDefinitionRepository,
    SqlGraphNodeDefinitionRepository,
    SqlGraphNodeTransitionDefinitionRepository,
    SqlRagDocumentRepository,
    SqlRunnerConfigRepository,
)
from shell.infrastructure.execution.persistence.sql.repositories import (
    SqlGraphExecutionRepository,
    SqlGraphExecutionStateInputRepository,
    SqlGraphNodeExecutionRepository,
    SqlGraphNodeExecutionStateRepository,
    SqlGraphNodeTransitionExecutionRepository,
    SqlTaskExecutionRepository,
    SqlTaskExecutionStateRepository,
    SqlWorkflowRepository,
    SqlWorkflowStateRepository,
)
from shell.infrastructure.platform.context import get_causation_id, get_correlation_id
from shell.infrastructure.platform.persistence.sql.models import OutboxEventModel
from shell.infrastructure.platform.persistence.sql.models.message.outbox_message import (
    OutboxMessageModel,
)
from shell.infrastructure.platform.persistence.sql.rag_search import create_rag_search_strategy
from shell.infrastructure.platform.persistence.sql.repositories.sql_message_repository import (
    SqlMessageRepository,
)
from shell.infrastructure.platform.serialization import DomainEventSerializer
from shell.infrastructure.session.persistence.sql.repositories.sql_session_repository import (
    SqlSessionRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.domain.platform.aggregates.message.message import Message
    from shell.domain.platform.events import DomainEvent

TRepository = TypeVar("TRepository")


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._factory = session_factory
        self._staged_events: list[DomainEvent] = []
        self._staged_messages: list[Message] = []
        self._committed = False
        self._session: AsyncSession | None = None
        self._rag_search_strategy = create_rag_search_strategy(session_factory)

    @property
    def _active_session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UnitOfWork not entered; use 'async with'")
        return self._session

    def repository(self, repo_type: type[TRepository]) -> TRepository:
        from shell.infrastructure.scheduling.persistence.sql.repositories.sql_scheduler_execution_repository import (
            SqlSchedulerExecutionRepository,
        )
        from shell.infrastructure.scheduling.persistence.sql.repositories.sql_scheduler_definition_repository import (
            SqlSchedulerDefinitionRepository,
        )

        domain_to_sql: dict[type, type] = {
            TaskExecutionRepository: SqlTaskExecutionRepository,
            TaskExecutionStateRepository: SqlTaskExecutionStateRepository,
            GraphExecutionRepository: SqlGraphExecutionRepository,
            GraphExecutionStateRepository: SqlGraphExecutionStateInputRepository,
            WorkflowRepository: SqlWorkflowRepository,
            WorkflowStateRepository: SqlWorkflowStateRepository,
            RunnerConfigRepository: SqlRunnerConfigRepository,
            RagDocumentRepository: SqlRagDocumentRepository,
            GraphDefinitionRepository: SqlGraphDefinitionRepository,
            GraphNodeDefinitionRepository: SqlGraphNodeDefinitionRepository,
            GraphNodeTransitionDefinitionRepository: SqlGraphNodeTransitionDefinitionRepository,
            GraphDefinitionEmbeddingRepository: SqlGraphDefinitionEmbeddingRepository,
            GraphNodeExecutionRepository: SqlGraphNodeExecutionRepository,
            GraphNodeExecutionStateRepository: SqlGraphNodeExecutionStateRepository,
            GraphNodeTransitionExecutionRepository: SqlGraphNodeTransitionExecutionRepository,
            MessageRepository: SqlMessageRepository,
            SessionRepository: SqlSessionRepository,
        }
        sql_type = domain_to_sql.get(repo_type)
        if sql_type is SqlRagDocumentRepository:
            return sql_type(self._active_session, search_strategy=self._rag_search_strategy)  # type: ignore[abstract, return-value]
        if sql_type is not None:
            return sql_type(self._active_session)
        if repo_type is SqlSchedulerDefinitionRepository:
            return SqlSchedulerDefinitionRepository(self._active_session)  # type: ignore[return-value]
        if repo_type is SqlSchedulerExecutionRepository:
            return SqlSchedulerExecutionRepository(self._active_session)  # type: ignore[return-value]
        msg = f"Unknown repository type: {repo_type}"
        raise ValueError(msg)

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._factory()
        await self._session.__aenter__()
        self._committed = False
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._session is not None:
            exc_type = args[0] if args else None
            if exc_type is None and not self._committed:
                await self.commit()
            await self._session.__aexit__(*args)
            self._session = None

    async def commit(self) -> None:
        from shell.infrastructure.platform.persistence.sql.mappers.message_mappers import (
            message_entity_to_model,
        )

        if self._session is None:
            return
        try:
            for event in self._staged_events:
                outbox = OutboxEventModel(
                    id=str(uuid.uuid4()),
                    event_type=type(event).__name__,
                    occurred_at=event.occurred_at.value,
                    payload=DomainEventSerializer().to_payload(event),
                    correlation_id=get_correlation_id(),
                    causation_id=get_causation_id(),
                )
                self._session.add(outbox)

            for message in self._staged_messages:
                model = message_entity_to_model(message)
                self._session.add(model)

                envelope = Envelope.from_message(
                    message=message,
                    trace_id=message.id.value,
                    sender_service="unknown",
                    receiver_service=message.destination.value,
                    correlation_id=get_correlation_id(),
                )
                OutboxMessageModel(
                    id=str(uuid.uuid4()),
                    envelope=envelope.to_dict(),
                    created_at=message.created_at.value,
                    published_at=None,
                )
                self._session.add(outbox)

            await self._session.commit()
            self._staged_events.clear()
            self._staged_messages.clear()
            self._committed = True
        except StaleDataError as exc:
            await self._session.rollback()
            raise ConcurrentModificationError("Aggregate", str(exc)) from exc

    async def rollback(self) -> None:
        if self._session is not None:
            await self._session.rollback()
        self._staged_events.clear()
        self._staged_messages.clear()

    def stage_events(self, events: list[DomainEvent]) -> None:
        self._staged_events.extend(events)

    def stage_messages(self, messages: list[Message]) -> None:
        self._staged_messages.extend(messages)
