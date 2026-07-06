from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from shell.application.platform.ports.unit_of_work import UnitOfWork
from shell.domain.definition.aggregates.graph_definition_embedding.repositories.graph_definition_embedding_repository import (
    GraphDefinitionEmbeddingRepository,
)
from shell.domain.definition.aggregates.node_link_definition.repositories.node_link_definition_repository import (
    NodeLinkDefinitionRepository,
)
from shell.domain.definition.repositories.graph_definition_repository.graph_definition_repository import (
    GraphDefinitionRepository,
)
from shell.domain.definition.repositories.graph_definition_repository.node_definition_repository import (
    NodeDefinitionRepository,
)
from shell.domain.definition.repositories.rag_repository import RagDocumentRepository
from shell.domain.definition.repositories.runner_config_repository import RunnerConfigRepository
from shell.domain.execution.aggregates.edge_execution.repositories.edge_execution_repository import (
    EdgeExecutionRepository,
)
from shell.domain.execution.aggregates.edge_link_execution.repositories.edge_link_execution_repository import (
    EdgeLinkExecutionRepository,
)
from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.graph_execution_state.repositories.graph_execution_state_repository import (
    GraphExecutionStateRepository,
)
from shell.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
    NodeExecutionRepository,
)
from shell.domain.execution.aggregates.node_execution_state.repositories.node_execution_state_repository import (
    NodeExecutionStateRepository,
)
from shell.domain.execution.aggregates.node_link_execution.repositories.node_link_execution_repository import (
    NodeLinkExecutionRepository,
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
from shell.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.infrastructure.definition.graph_definition.persistence.memory.in_memory_graph_definition_repository import (
    InMemoryGraphDefinitionRepository,
)
from shell.infrastructure.definition.graph_definition_embedding.persistence.memory.in_memory_graph_definition_embedding_repository import (
    InMemoryGraphDefinitionEmbeddingRepository,
)
from shell.infrastructure.definition.node_definition.persistence.memory.in_memory_node_definition_repository import (
    InMemoryNodeDefinitionRepository,
)
from shell.infrastructure.definition.node_link_definition.persistence.memory.in_memory_node_link_definition_repository import (
    InMemoryNodeLinkDefinitionRepository,
)
from shell.infrastructure.definition.rag_document.persistence.memory.in_memory_rag_document_repository import (
    InMemoryRagDocumentRepository,
)
from shell.infrastructure.definition.runner_config.persistence.memory.in_memory_runner_config_repository import (
    InMemoryRunnerConfigRepository,
)
from shell.infrastructure.execution.edge_execution.persistence.memory.in_memory_edge_execution_repository import (
    InMemoryEdgeExecutionRepository,
)
from shell.infrastructure.execution.edge_link_execution.persistence.memory.in_memory_edge_link_execution_repository import (
    InMemoryEdgeLinkExecutionRepository,
)
from shell.infrastructure.execution.graph_execution.persistence.memory.in_memory_graph_execution_repository import (
    InMemoryGraphExecutionRepository,
)
from shell.infrastructure.execution.node_execution.persistence.memory.in_memory_node_execution_repository import (
    InMemoryNodeExecutionRepository,
)
from shell.infrastructure.execution.node_execution_state.persistence.memory.in_memory_node_execution_state_repository import (
    InMemoryNodeExecutionStateRepository,
)
from shell.infrastructure.execution.node_link_execution.persistence.memory.in_memory_node_link_execution_repository import (
    InMemoryNodeLinkExecutionRepository,
)
from shell.infrastructure.execution.task_execution.persistence.memory.in_memory_task_execution_repository import (
    InMemoryTaskExecutionRepository,
)
from shell.infrastructure.execution.task_execution_state.persistence.memory.in_memory_task_execution_state_repository import (
    InMemoryTaskExecutionStateRepository,
)
from shell.infrastructure.execution.workflow.persistence.memory.in_memory_workflow_repository import (
    InMemoryWorkflowRepository,
)
from shell.infrastructure.execution.workflow_state.persistence.memory.in_memory_workflow_state_repository import (
    InMemoryWorkflowStateRepository,
)
from shell.infrastructure.platform.persistence.memory.in_memory_graph_execution_state_input_repository import (
    InMemoryGraphExecutionStateRepository,
)
from shell.infrastructure.platform.persistence.memory.in_memory_message_repository import (
    InMemoryMessageRepository,
)
from shell.infrastructure.session.session.persistence.memory.in_memory_session_repository import (
    InMemorySessionRepository,
)

if TYPE_CHECKING:
    from shell.domain.platform.aggregates.message.message import Message
    from shell.domain.platform.events import DomainEvent

from datetime import UTC, datetime

from shell.domain.definition.aggregates.graph_definition.graph_definition import (
    GraphDefinition,
)
from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.domain.definition.aggregates.node_definition.node_definition import (
    NodeDefinition,
)
from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
    NodeDefinitionId,
)
from shell.domain.definition.aggregates.node_link_definition.node_link_definition import (
    NodeLinkDefinition,
)
from shell.domain.definition.aggregates.node_link_definition.value_objects.node_link_definition_id import (
    NodeLinkDefinitionId,
)
from shell.domain.definition.value_objects.node_role_name import NodeRoleName
from shell.domain.definition.value_objects.node_type_name import NodeTypeName
from shell.domain.platform.value_objects.mode import Mode

TRepository = TypeVar("TRepository")


class InMemoryUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self._task_execution_repository = InMemoryTaskExecutionRepository()
        self._task_execution_state_repository = InMemoryTaskExecutionStateRepository()
        self._node_execution_repository = InMemoryNodeExecutionRepository()
        self._node_link_execution_repository = InMemoryNodeLinkExecutionRepository()
        self._node_execution_repository.set_link_repo(self._node_link_execution_repository)
        self._graph_execution_repository = InMemoryGraphExecutionRepository()
        self._graph_execution_repository.link_task_executions(self._task_execution_repository)
        self._workflow_repository = InMemoryWorkflowRepository()
        self._runner_config_repository = InMemoryRunnerConfigRepository()
        self._rag_document_repository = InMemoryRagDocumentRepository()
        self._graph_definition_repository = InMemoryGraphDefinitionRepository()
        self._node_definition_repository = InMemoryNodeDefinitionRepository()
        self._node_link_definition_repository = InMemoryNodeLinkDefinitionRepository()
        self._node_definition_repository.set_link_repo(self._node_link_definition_repository)
        self._graph_definition_embedding_repository = InMemoryGraphDefinitionEmbeddingRepository()
        self._edge_execution_repository = InMemoryEdgeExecutionRepository()
        self._edge_link_execution_repository = InMemoryEdgeLinkExecutionRepository()
        self._node_execution_state_repository = InMemoryNodeExecutionStateRepository()
        self._graph_execution_state_repository = InMemoryGraphExecutionStateRepository()
        self._workflow_state_repository = InMemoryWorkflowStateRepository()
        self._message_repository = InMemoryMessageRepository()
        self._session_repository = InMemorySessionRepository()

        self._committed = False
        self._staged_events: list[DomainEvent] = []
        self._staged_messages: list[Message] = []
        self._committed_events: list[DomainEvent] = []

    async def seed_base_planner(self) -> None:
        now = datetime.now(UTC)
        node_id = NodeDefinitionId("base-planner-node-1")
        graph_id = GraphDefinitionId("base-planner-id")

        node = NodeDefinition.create(
            id=node_id,
            mode=Mode("agent"),
            role=NodeRoleName("agent"),
            node_type=NodeTypeName("agent"),
            now=now,
        )
        await self.repository(InMemoryNodeDefinitionRepository).save(node)

        graph = GraphDefinition.create(
            id=graph_id,
            now=now,
        )
        await self.repository(InMemoryGraphDefinitionRepository).save(graph)

        link = NodeLinkDefinition(
            id=NodeLinkDefinitionId.generate(),
            graph_definition_id=graph_id,
            node_definition_id=node_id,
        )
        await self.repository(InMemoryNodeLinkDefinitionRepository).save(link)

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
            InMemoryNodeDefinitionRepository: self._node_definition_repository,
            NodeDefinitionRepository: self._node_definition_repository,
            InMemoryNodeLinkDefinitionRepository: self._node_link_definition_repository,
            NodeLinkDefinitionRepository: self._node_link_definition_repository,
            InMemoryGraphDefinitionEmbeddingRepository: self._graph_definition_embedding_repository,
            GraphDefinitionEmbeddingRepository: self._graph_definition_embedding_repository,
            InMemoryGraphExecutionStateRepository: self._graph_execution_state_repository,
            GraphExecutionStateRepository: self._graph_execution_state_repository,
            InMemoryNodeExecutionRepository: self._node_execution_repository,
            NodeExecutionRepository: self._node_execution_repository,
            InMemoryNodeExecutionStateRepository: self._node_execution_state_repository,
            NodeExecutionStateRepository: self._node_execution_state_repository,
            InMemoryNodeLinkExecutionRepository: self._node_link_execution_repository,
            NodeLinkExecutionRepository: self._node_link_execution_repository,
            InMemoryEdgeExecutionRepository: self._edge_execution_repository,
            EdgeExecutionRepository: self._edge_execution_repository,
            InMemoryEdgeLinkExecutionRepository: self._edge_link_execution_repository,
            EdgeLinkExecutionRepository: self._edge_link_execution_repository,
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

    async def save(self, repo_type: type, aggregate: Any) -> None:
        repo: Any = self.repository(repo_type)
        await repo.save(aggregate)
        self.stage_events(aggregate.pull_events())

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
