from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from shell.execution_service.domain.execution.aggregates.edge_execution.repositories.edge_execution_repository import (
    EdgeExecutionRepository,
)
from shell.execution_service.domain.execution.aggregates.edge_link_execution.repositories.edge_link_execution_repository import (
    EdgeLinkExecutionRepository,
)
from shell.execution_service.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.execution_service.domain.execution.aggregates.graph_execution_state.repositories.graph_execution_state_repository import (
    GraphExecutionStateRepository,
)
from shell.execution_service.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
    NodeExecutionRepository,
)
from shell.execution_service.domain.execution.aggregates.node_execution_state.repositories.node_execution_state_repository import (
    NodeExecutionStateRepository,
)
from shell.execution_service.domain.execution.aggregates.node_link_execution.repositories.node_link_execution_repository import (
    NodeLinkExecutionRepository,
)
from shell.execution_service.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.execution_service.domain.execution.aggregates.task_execution_state.repositories.task_execution_state_repository import (
    TaskExecutionStateRepository,
)
from shell.execution_service.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.execution_service.domain.execution.aggregates.workflow_state.repositories.workflow_state_repository import (
    WorkflowStateRepository,
)
from shell.execution_service.infrastructure.execution.edge_execution.persistence.memory.in_memory_edge_execution_repository import (
    InMemoryEdgeExecutionRepository,
)
from shell.execution_service.infrastructure.execution.edge_link_execution.persistence.memory.in_memory_edge_link_execution_repository import (
    InMemoryEdgeLinkExecutionRepository,
)
from shell.execution_service.infrastructure.execution.graph_execution.persistence.memory.in_memory_graph_execution_repository import (
    InMemoryGraphExecutionRepository,
)
from shell.execution_service.infrastructure.execution.graph_execution_state.persistence.memory.in_memory_graph_execution_state_repository import (
    InMemoryGraphExecutionStateRepository,
)
from shell.execution_service.infrastructure.execution.node_execution.persistence.memory.in_memory_node_execution_repository import (
    InMemoryNodeExecutionRepository,
)
from shell.execution_service.infrastructure.execution.node_execution_state.persistence.memory.in_memory_node_execution_state_repository import (
    InMemoryNodeExecutionStateRepository,
)
from shell.execution_service.infrastructure.execution.node_link_execution.persistence.memory.in_memory_node_link_execution_repository import (
    InMemoryNodeLinkExecutionRepository,
)
from shell.execution_service.infrastructure.execution.task_execution.persistence.memory.in_memory_task_execution_repository import (
    InMemoryTaskExecutionRepository,
)
from shell.execution_service.infrastructure.execution.task_execution_state.persistence.memory.in_memory_task_execution_state_repository import (
    InMemoryTaskExecutionStateRepository,
)
from shell.execution_service.infrastructure.execution.workflow.persistence.memory.in_memory_workflow_repository import (
    InMemoryWorkflowRepository,
)
from shell.execution_service.infrastructure.execution.workflow_state.persistence.memory.in_memory_workflow_state_repository import (
    InMemoryWorkflowStateRepository,
)
from shell.platform.application.ports.persistence.unit_of_work import UnitOfWork

if TYPE_CHECKING:
    from collections.abc import Sequence

    from shell.platform.domain.events import DomainEvent

TRepository = TypeVar("TRepository")


class InMemoryExecutionUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self._task_execution_repository = InMemoryTaskExecutionRepository()
        self._task_execution_state_repository = InMemoryTaskExecutionStateRepository()
        self._node_execution_repository = InMemoryNodeExecutionRepository()
        self._node_link_execution_repository = InMemoryNodeLinkExecutionRepository()
        self._node_execution_repository.set_link_repository(self._node_link_execution_repository)
        self._graph_execution_repository = InMemoryGraphExecutionRepository()
        self._graph_execution_repository.link_task_executions(self._task_execution_repository)
        self._workflow_repository = InMemoryWorkflowRepository()
        self._edge_execution_repository = InMemoryEdgeExecutionRepository()
        self._edge_link_execution_repository = InMemoryEdgeLinkExecutionRepository()
        self._node_execution_state_repository = InMemoryNodeExecutionStateRepository()
        self._graph_execution_state_repository = InMemoryGraphExecutionStateRepository()
        self._workflow_state_repository = InMemoryWorkflowStateRepository()

        self._committed = False
        self._staged_events: list[DomainEvent] = []
        self._committed_events: list[DomainEvent] = []

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
            InMemoryGraphExecutionStateRepository: self._graph_execution_state_repository,
            GraphExecutionStateRepository: self._graph_execution_state_repository,
        }
        repo = repos.get(repo_type)
        if repo is None:
            msg = f"Unknown repository type: {repo_type}"
            raise ValueError(msg)
        return repo  # type: ignore[return-value]

    def stage_events(self, events: Sequence[object]) -> None:
        self._staged_events.extend(events)  # type: ignore[arg-type]

    async def save(self, repo_type: type, aggregate: object) -> None:
        repo: Any = self.repository(repo_type)
        await repo.save(aggregate)
        self.stage_events(aggregate.pull_events())  # type: ignore[attr-defined]

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._staged_events)

    @property
    def committed_events(self) -> list[DomainEvent]:
        return list(self._committed_events)

    async def __aenter__(self) -> InMemoryExecutionUnitOfWork:
        self._committed = False
        self._staged_events = []
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
        self._staged_events.clear()

    async def rollback(self) -> None:
        self._staged_events.clear()
