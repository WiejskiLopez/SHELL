from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.platform.ports.unit_of_work import UnitOfWork
from shell.infrastructure.definition.persistence.memory.in_memory_graph_definition_repository import (
    InMemoryGraphDefinitionRepository,
)
from shell.infrastructure.definition.persistence.memory.in_memory_rag_document_repository import (
    InMemoryRagDocumentRepository,
)
from shell.infrastructure.definition.persistence.memory.in_memory_runner_config_repository import (
    InMemoryRunnerConfigRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_graph_execution_repository import (
    InMemoryGraphExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_graph_node_execution_repository import (
    InMemoryGraphNodeExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_graph_node_execution_state_repository import (
    InMemoryGraphNodeExecutionStateRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_graph_node_transition_execution_repository import (
    InMemoryGraphNodeTransitionExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_task_execution_repository import (
    InMemoryTaskExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_task_execution_state_repository import (
    InMemoryTaskExecutionStateRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_workflow_repository import (
    InMemoryWorkflowRepository,
)
from shell.infrastructure.platform.persistence.memory.in_memory_graph_execution_state_input_repository import (
    InMemoryGraphExecutionStateRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_workflow_state_repository import (
    InMemoryWorkflowStateRepository,
)
from shell.infrastructure.platform.persistence.memory.in_memory_message_repository import (
    InMemoryMessageRepository,
)
from shell.infrastructure.session.persistence.memory.in_memory_session_repository import (
    InMemorySessionRepository,
)

if TYPE_CHECKING:
    from shell.domain.platform.aggregates.message.message import Message
    from shell.domain.platform.events import DomainEvent


class InMemoryUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self._task_execution_repository = InMemoryTaskExecutionRepository()
        self._task_execution_state_repository = InMemoryTaskExecutionStateRepository()
        self._graph_node_execution_repository = InMemoryGraphNodeExecutionRepository()
        self._graph_execution_repository = InMemoryGraphExecutionRepository()
        self._graph_execution_repository.link_task_executions(self._task_execution_repository)
        self._workflow_repository = InMemoryWorkflowRepository()
        self._runner_config_repository = InMemoryRunnerConfigRepository()
        self._rag_document_repository = InMemoryRagDocumentRepository()
        self._graph_definition_repository = InMemoryGraphDefinitionRepository()
        self._graph_node_transition_execution_repository = InMemoryGraphNodeTransitionExecutionRepository()
        self._graph_node_execution_state_repository = InMemoryGraphNodeExecutionStateRepository()
        self._graph_execution_state_repository = InMemoryGraphExecutionStateRepository()
        self._workflow_state_repository = InMemoryWorkflowStateRepository()
        self._message_repository = InMemoryMessageRepository()
        self._session_repository = InMemorySessionRepository()

        self._committed = False
        self._staged_events: list[DomainEvent] = []
        self._staged_messages: list[Message] = []
        self._committed_events: list[DomainEvent] = []

    async def seed_base_planner(self) -> None:
        from shell.domain.definition.entities.graph_definition import GraphDefinition
        from shell.domain.definition.entities.graph_node_definition import GraphNodeDefinition
        from shell.domain.definition.value_objects.ids import (
            GraphDefinitionId,
            GraphNodeDefinitionId,
        )
        from shell.domain.platform.value_objects.mode import Mode

        await self._graph_definition_repository.save(
            GraphDefinition(
                id=GraphDefinitionId("base-planner-id"),
                name="base_planner",
                purpose="default_planning",
                graph_node_definitions=[
                    GraphNodeDefinition(
                        id=GraphNodeDefinitionId("base-planner-node-1"),
                        position=0,
                        mode=Mode("agent"),
                        role="agent",
                        node_type="agent",
                    ),
                ],
            )
        )

    @property
    def task_execution_repository(self) -> InMemoryTaskExecutionRepository:
        return self._task_execution_repository

    @property
    def task_execution_state_repository(self) -> InMemoryTaskExecutionStateRepository:
        return self._task_execution_state_repository

    @property
    def graph_execution_repository(self) -> InMemoryGraphExecutionRepository:
        return self._graph_execution_repository

    @property
    def workflow_repository(self) -> InMemoryWorkflowRepository:
        return self._workflow_repository

    @property
    def runner_config_repository(self) -> InMemoryRunnerConfigRepository:
        return self._runner_config_repository

    @property
    def rag_document_repository(self) -> InMemoryRagDocumentRepository:
        return self._rag_document_repository

    @property
    def workflow_state_repository(self) -> InMemoryWorkflowStateRepository:
        return self._workflow_state_repository

    @property
    def session_repository(self) -> InMemorySessionRepository:
        return self._session_repository

    @property
    def graph_definition_repository(self) -> InMemoryGraphDefinitionRepository:
        return self._graph_definition_repository

    @property
    def graph_execution_state_repository(self) -> InMemoryGraphExecutionStateRepository:
        return self._graph_execution_state_repository

    @property
    def graph_node_execution_repository(self) -> InMemoryGraphNodeExecutionRepository:
        return self._graph_node_execution_repository

    @property
    def graph_node_execution_state_repository(self) -> InMemoryGraphNodeExecutionStateRepository:
        return self._graph_node_execution_state_repository

    @property
    def graph_node_transition_execution_repository(self) -> InMemoryGraphNodeTransitionExecutionRepository:
        return self._graph_node_transition_execution_repository

    @property
    def workflow_state_repository(self) -> InMemoryWorkflowStateRepository:
        return self._workflow_state_repository

    @property
    def message_repository(self) -> InMemoryMessageRepository:
        return self._message_repository

    @property
    def session_repository(self) -> InMemorySessionRepository:
        return self._session_repository

    def stage_events(self, events: list[DomainEvent]) -> None:
        self._staged_events.extend(events)

    def stage_messages(self, messages: list[Message]) -> None:
        self._staged_messages.extend(messages)

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._staged_events)

    @property
    def committed_events(self) -> list[DomainEvent]:
        return list(self._committed_events)

    async def __aenter__(self) -> InMemoryUnitOfWork:
        self._committed = False
        self._staged_events = []
        self._staged_messages = []
        self._committed_events = []
        return self

    async def __aexit__(self, *args: object) -> None:
        if args[0] is None:
            await self.commit()
        else:
            await self.rollback()

    async def commit(self) -> None:
        self._committed = True
        self._committed_events.extend(self._staged_events)
        for message in self._staged_messages:
            await self._message_repository.save(message)
        self._staged_events.clear()
        self._staged_messages.clear()

    async def rollback(self) -> None:
        self._staged_events.clear()
        self._staged_messages.clear()

    async def rollback(self) -> None:
        self._staged_events.clear()
