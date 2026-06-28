from __future__ import annotations

from typing import TypeVar

from shell.application.platform.ports.unit_of_work import UnitOfWork

TRepository = TypeVar("TRepository")
from shell.infrastructure.definition.persistence.memory.in_memory_graph_definition_repository import (
    InMemoryGraphDefinitionRepository,
)
from shell.infrastructure.definition.persistence.memory.in_memory_graph_definition_embedding_repository import (
    InMemoryGraphDefinitionEmbeddingRepository,
)
from shell.infrastructure.definition.persistence.memory.in_memory_graph_node_definition_repository import (
    InMemoryGraphNodeDefinitionRepository,
)
from shell.infrastructure.definition.persistence.memory.in_memory_graph_node_transition_definition_repository import (
    InMemoryGraphNodeTransitionDefinitionRepository,
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
from shell.infrastructure.execution.persistence.memory.in_memory_workflow_state_repository import (
    InMemoryWorkflowStateRepository,
)
from shell.infrastructure.platform.persistence.memory.in_memory_graph_execution_state_input_repository import (
    InMemoryGraphExecutionStateRepository,
)
from shell.infrastructure.platform.persistence.memory.in_memory_message_repository import (
    InMemoryMessageRepository,
)
from shell.infrastructure.session.persistence.memory.in_memory_session_repository import (
    InMemorySessionRepository,
)

from shell.domain.definition.repositories.graph_definition_repository.graph_definition_repository import (
    GraphDefinitionRepository,
)
from shell.domain.definition.repositories.graph_definition_repository.graph_node_definition_repository import (
    GraphNodeDefinitionRepository,
)
from shell.domain.definition.aggregates.graph_node_transition_definition.repositories.graph_node_transition_definition_repository import (
    GraphNodeTransitionDefinitionRepository,
)
from shell.domain.definition.aggregates.graph_definition_embedding.repositories.graph_definition_embedding_repository import (
    GraphDefinitionEmbeddingRepository,
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
from shell.domain.platform.aggregates.message.message import Message
from shell.domain.platform.aggregates.message.repositories.message_repository import (
    MessageRepository,
)
from shell.domain.platform.events import DomainEvent
from shell.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)


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
        self._graph_node_definition_repository = InMemoryGraphNodeDefinitionRepository()
        self._graph_node_transition_definition_repository = InMemoryGraphNodeTransitionDefinitionRepository()
        self._graph_definition_embedding_repository = InMemoryGraphDefinitionEmbeddingRepository()
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
        from datetime import UTC, datetime

        from shell.domain.definition.aggregates.graph_definition.graph_definition import (
            GraphDefinition,
        )
        from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
            GraphDefinitionId,
        )
        from shell.domain.definition.aggregates.graph_node_definition.graph_node_definition import (
            GraphNodeDefinition,
        )
        from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
            GraphNodeDefinitionId,
        )
        from shell.domain.definition.value_objects.graph_name import GraphName
        from shell.domain.definition.value_objects.node_position import NodePosition
        from shell.domain.definition.value_objects.node_role_name import NodeRoleName
        from shell.domain.definition.value_objects.node_type_name import NodeTypeName
        from shell.domain.definition.value_objects.purpose import Purpose
        from shell.domain.platform.value_objects.mode import Mode

        now = datetime.now(UTC)
        node_id = GraphNodeDefinitionId("base-planner-node-1")
        graph_id = GraphDefinitionId("base-planner-id")

        node = GraphNodeDefinition.create(
            id=node_id,
            graph_definition_id=graph_id,
            position=NodePosition(0),
            mode=Mode("agent"),
            role=NodeRoleName("agent"),
            node_type=NodeTypeName("agent"),
            now=now,
        )
        await self.repository(InMemoryGraphNodeDefinitionRepository).save(node)

        from shell.domain.definition.value_objects.system_role import SystemRole

        graph = GraphDefinition.create(
            id=graph_id,
            name=GraphName("base_planner"),
            purpose=Purpose("default_planning"),
            system_role=SystemRole.PLANNER,
            graph_node_definition_ids=[node_id],
            now=now,
        )
        await self.repository(InMemoryGraphDefinitionRepository).save(graph)

    def repository(self, repo_type: type[TRepository]) -> TRepository:
        repos: dict[type, object] = {
            InMemoryTaskExecutionRepository: self._task_execution_repository,
            TaskExecutionRepository: self._task_execution_repository,
            InMemoryTaskExecutionStateRepository: self._task_execution_state_repository,
            TaskExecutionStateRepository: self._task_execution_state_repository,
            InMemoryGraphExecutionRepository: self._graph_execution_repository,
            GraphExecutionRepository: self._graph_execution_repository,
            InMemoryWorkflowRepository: self._workflow_repository,
            WorkflowRepository: self._workflow_repository,
            InMemoryRunnerConfigRepository: self._runner_config_repository,
            RunnerConfigRepository: self._runner_config_repository,
            InMemoryRagDocumentRepository: self._rag_document_repository,
            RagDocumentRepository: self._rag_document_repository,
            InMemoryGraphDefinitionRepository: self._graph_definition_repository,
            GraphDefinitionRepository: self._graph_definition_repository,
            InMemoryGraphNodeDefinitionRepository: self._graph_node_definition_repository,
            GraphNodeDefinitionRepository: self._graph_node_definition_repository,
            InMemoryGraphNodeTransitionDefinitionRepository: self._graph_node_transition_definition_repository,
            GraphNodeTransitionDefinitionRepository: self._graph_node_transition_definition_repository,
            InMemoryGraphDefinitionEmbeddingRepository: self._graph_definition_embedding_repository,
            GraphDefinitionEmbeddingRepository: self._graph_definition_embedding_repository,
            InMemoryGraphExecutionStateRepository: self._graph_execution_state_repository,
            GraphExecutionStateRepository: self._graph_execution_state_repository,
            InMemoryGraphNodeExecutionRepository: self._graph_node_execution_repository,
            GraphNodeExecutionRepository: self._graph_node_execution_repository,
            InMemoryGraphNodeExecutionStateRepository: self._graph_node_execution_state_repository,
            GraphNodeExecutionStateRepository: self._graph_node_execution_state_repository,
            InMemoryGraphNodeTransitionExecutionRepository: self._graph_node_transition_execution_repository,
            GraphNodeTransitionExecutionRepository: self._graph_node_transition_execution_repository,
            InMemoryWorkflowStateRepository: self._workflow_state_repository,
            WorkflowStateRepository: self._workflow_state_repository,
            InMemoryMessageRepository: self._message_repository,
            MessageRepository: self._message_repository,
            InMemorySessionRepository: self._session_repository,
            SessionRepository: self._session_repository,
        }
        repo = repos.get(repo_type)
        if repo is None:
            msg = f"Unknown repository type: {repo_type}"
            raise ValueError(msg)
        return repo  # type: ignore[return-value]

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
