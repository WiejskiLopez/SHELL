from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, TypeVar

from shell.definition_service.domain.definition.aggregates.graph_definition.graph_definition import (
    GraphDefinition,
)
from shell.definition_service.domain.definition.aggregates.graph_definition.repositories.graph_definition_repository import (
    GraphDefinitionRepository,
)
from shell.definition_service.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.definition_service.domain.definition.aggregates.graph_definition_embedding.repositories.graph_definition_embedding_repository import (
    GraphDefinitionEmbeddingRepository,
)
from shell.definition_service.domain.definition.aggregates.node_definition.node_definition import (
    NodeDefinition,
)
from shell.definition_service.domain.definition.aggregates.node_definition.repositories.node_definition_repository import (
    NodeDefinitionRepository,
)
from shell.definition_service.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
    NodeDefinitionId,
)
from shell.definition_service.domain.definition.aggregates.node_definition.value_objects.node_type import (
    NodeType,
)
from shell.definition_service.domain.definition.aggregates.node_link_definition.node_link_definition import (
    NodeLinkDefinition,
)
from shell.definition_service.domain.definition.aggregates.node_link_definition.repositories.node_link_definition_repository import (
    NodeLinkDefinitionRepository,
)
from shell.definition_service.domain.definition.aggregates.node_link_definition.value_objects.node_link_definition_id import (
    NodeLinkDefinitionId,
)
from shell.definition_service.domain.definition.aggregates.runner_config.repositories.runner_config_repository import (
    RunnerConfigRepository,
)
from shell.definition_service.infrastructure.definition.graph_definition.persistence.memory.in_memory_graph_definition_repository import (
    InMemoryGraphDefinitionRepository,
)
from shell.definition_service.infrastructure.definition.graph_definition_embedding.persistence.memory.in_memory_graph_definition_embedding_repository import (
    InMemoryGraphDefinitionEmbeddingRepository,
)
from shell.definition_service.infrastructure.definition.node_definition.persistence.memory.in_memory_node_definition_repository import (
    InMemoryNodeDefinitionRepository,
)
from shell.definition_service.infrastructure.definition.node_link_definition.persistence.memory.in_memory_node_link_definition_repository import (
    InMemoryNodeLinkDefinitionRepository,
)
from shell.definition_service.infrastructure.definition.runner_config.persistence.memory.in_memory_runner_config_repository import (
    InMemoryRunnerConfigRepository,
)
from shell.platform.application.ports.persistence.unit_of_work import UnitOfWork
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from collections.abc import Sequence

    from shell.platform.domain.events import DomainEvent

TRepository = TypeVar("TRepository")


class InMemoryDefinitionUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self._runner_config_repository = InMemoryRunnerConfigRepository()
        self._graph_definition_repository = InMemoryGraphDefinitionRepository()
        self._node_definition_repository = InMemoryNodeDefinitionRepository()
        self._node_link_definition_repository = InMemoryNodeLinkDefinitionRepository()
        self._node_definition_repository.set_link_repository(self._node_link_definition_repository)
        self._graph_definition_embedding_repository = InMemoryGraphDefinitionEmbeddingRepository()

        self._committed = False
        self._staged_events: list[DomainEvent] = []
        self._staged_messages: list[object] = []
        self._committed_events: list[DomainEvent] = []

    async def seed_base_planner(self) -> None:
        now = CreatedAt.from_datetime(datetime.now(UTC))
        node_id = NodeDefinitionId("base-planner-node-1")
        graph_id = GraphDefinitionId("base-planner-id")

        node = NodeDefinition.create(
            id=node_id,
            node_type=NodeType("agent"),
            now=now,
        )
        await self.repository(InMemoryNodeDefinitionRepository).save(node)

        graph = GraphDefinition.create(
            id=graph_id,
            now=now,
        )
        await self.repository(InMemoryGraphDefinitionRepository).save(graph)

        link = NodeLinkDefinition.restore(
            id=NodeLinkDefinitionId.generate(),
            created_at=now,
            graph_definition_id=graph_id,
            node_definition_id=node_id,
        )
        await self.repository(InMemoryNodeLinkDefinitionRepository).save(link)

    def repository(self, repo_type: type[TRepository]) -> TRepository:
        repos: dict[type, object] = {
            InMemoryRunnerConfigRepository: self._runner_config_repository,
            RunnerConfigRepository: self._runner_config_repository,
            InMemoryGraphDefinitionRepository: self._graph_definition_repository,
            GraphDefinitionRepository: self._graph_definition_repository,
            InMemoryNodeDefinitionRepository: self._node_definition_repository,
            NodeDefinitionRepository: self._node_definition_repository,
            InMemoryNodeLinkDefinitionRepository: self._node_link_definition_repository,
            NodeLinkDefinitionRepository: self._node_link_definition_repository,
            InMemoryGraphDefinitionEmbeddingRepository: self._graph_definition_embedding_repository,
            GraphDefinitionEmbeddingRepository: self._graph_definition_embedding_repository,
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
        self.stage_messages(aggregate.pull_messages())  # type: ignore[attr-defined]

    def stage_messages(self, messages: list[object]) -> None:
        self._staged_messages.extend(messages)

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._staged_events)

    @property
    def committed_events(self) -> list[DomainEvent]:
        return list(self._committed_events)

    async def __aenter__(self) -> InMemoryDefinitionUnitOfWork:
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
        self._staged_events.clear()
        self._staged_messages.clear()

    async def rollback(self) -> None:
        self._staged_events.clear()
