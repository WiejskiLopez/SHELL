"""Unit tests for ``BuildGraphExecutionOnTaskExecutionCreatedEventHandler`` event handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from shell.application.execution.event_handlers.build_graph_execution_on_task_execution_created_event_handler import (
    BuildGraphExecutionOnTaskExecutionCreatedEventHandler,
)
from shell.application.definition.exceptions.graph_definition_not_found_exception import GraphDefinitionNotFoundException
from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
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
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_initialized_event import (
    GraphExecutionInitializedEvent,
)
from shell.domain.execution.aggregates.graph_execution.ports.graph_definition_semantic_query import (
    GraphDefinitionSemanticQuery,
)
from shell.domain.execution.events import TaskExecutionCreatedEvent
from shell.domain.execution.value_objects.graph_execution_definition import (
    GraphExecutionDefinition,
    GraphNodeExecutionDefinition,
)
from shell.domain.execution.value_objects.graph_execution_initialization_status import (
    GraphExecutionInitializationStatus,
)
from shell.domain.execution.value_objects.ids import TaskExecutionId
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.platform.value_objects.mode import Mode
from shell.infrastructure.definition.persistence.memory.in_memory_graph_definition_repository import (
    InMemoryGraphDefinitionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_graph_node_execution_repository import (
    InMemoryGraphNodeExecutionRepository,
)
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeIdGenerator,
    FakeLogger,
    InMemoryGraphExecutionRepository,
    InMemoryGraphNodeDefinitionRepository,
    InMemoryUnitOfWork,
)

if TYPE_CHECKING:
    from datetime import datetime


class _InMemoryGraphDefinitionQueryService:
    def __init__(self, unit_of_work: InMemoryUnitOfWork) -> None:
        self._repo = unit_of_work.repository(InMemoryGraphDefinitionRepository)
        self._node_repo = unit_of_work.repository(InMemoryGraphNodeDefinitionRepository)

    async def get_graph_definition_by_semantic_name(
        self, query: GraphDefinitionSemanticQuery,
    ) -> GraphExecutionDefinition | None:
        if query.default_graph_definition is not None:
            for entity in (await self._repo.list_all()):
                if entity.system_role is not None and entity.system_role.value == query.default_graph_definition:
                    return await self._to_dto(entity)
        entity = await self._repo.get_graph_definition_by_name(GraphName(query.text))
        if entity is None:
            return None
        return await self._to_dto(entity)

    async def get_graph_definition(self, definition_id: str) -> GraphExecutionDefinition | None:
        from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
            GraphDefinitionId,
        )

        entity = await self._repo.get_by_id(GraphDefinitionId(definition_id))
        if entity is None:
            return None
        return await self._to_dto(entity)

    async def _to_dto(self, entity: object) -> GraphExecutionDefinition:
        graph_definition: GraphDefinition = entity  # type: ignore[assignment]
        nodes: list[GraphNodeDefinition] = []
        for node_id in graph_definition.graph_node_definition_ids:
            node = await self._node_repo.get_by_id(node_id)
            if node is not None:
                nodes.append(node)
        return GraphExecutionDefinition(
            id=graph_definition.id.value,
            name=graph_definition.name.value,
            graph_node_execution_definitions=[
                GraphNodeExecutionDefinition(
                    position=node.position.value,
                    mode=node.mode.value,
                    role=node.role.value,
                    node_type=node.node_type.value,
                    model=node.model.value if node.model else "",
                    command=node.command.value if node.command else "",
                    timeout=node.timeout.value if node.timeout else 0,
                    retries=node.retries.value if node.retries else 0,
                    log_level=node.log_level.value if node.log_level else "INFO",
                    max_step=node.max_step.value if node.max_step else None,
                    no_ask_user=node.no_ask_user.value if node.no_ask_user else False,
                    autopilot=node.autopilot.value if node.autopilot else False,
                    status_initial=node.status_initial.value if node.status_initial else "",
                    script=node.script.value if node.script else "",
                    script_type=node.script_type.value if node.script_type else "",
                )
                for node in nodes
            ],
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def unit_of_work() -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork()


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture()
def id_generator() -> FakeIdGenerator:
    return FakeIdGenerator()


@pytest.fixture()
def logger() -> FakeLogger:
    return FakeLogger()


async def _seed_graph_definition(
    unit_of_work: InMemoryUnitOfWork, name: str = "base_planner"
) -> GraphDefinition:
    from datetime import UTC, datetime

    from shell.domain.definition.value_objects.node_position import NodePosition
    from shell.domain.definition.value_objects.node_role_name import NodeRoleName
    from shell.domain.definition.value_objects.node_type_name import NodeTypeName
    from shell.domain.definition.value_objects.purpose import Purpose
    from shell.domain.definition.value_objects.system_role import SystemRole

    now = datetime.now(UTC)
    node1_id = GraphNodeDefinitionId("tn-1")
    node2_id = GraphNodeDefinitionId("tn-2")

    node1 = GraphNodeDefinition.create(
        id=node1_id,
        graph_definition_id=GraphDefinitionId(f"{name}-id"),
        position=NodePosition(0),
        mode=Mode("agent"),
        role=NodeRoleName("agent"),
        node_type=NodeTypeName("agent"),
        now=now,
    )
    node2 = GraphNodeDefinition.create(
        id=node2_id,
        graph_definition_id=GraphDefinitionId(f"{name}-id"),
        position=NodePosition(1),
        mode=Mode("worker"),
        role=NodeRoleName("worker"),
        node_type=NodeTypeName("worker"),
        now=now,
    )
    await unit_of_work.repository(InMemoryGraphNodeDefinitionRepository).save(node1)
    await unit_of_work.repository(InMemoryGraphNodeDefinitionRepository).save(node2)

    repo = unit_of_work.repository(InMemoryGraphDefinitionRepository)
    keys_to_remove = [k for k, v in repo._store.items() if v.name == name]
    for k in keys_to_remove:
        del repo._store[k]

    graph_definition = GraphDefinition.create(
        id=GraphDefinitionId(f"{name}-id"),
        name=GraphName(name),
        purpose=Purpose("planning"),
        system_role=SystemRole.PLANNER,
        graph_node_definition_ids=[node1_id, node2_id],
        now=now,
    )
    await repo.save(graph_definition)
    return graph_definition


def _task_created_event(now: datetime) -> TaskExecutionCreatedEvent:
    return TaskExecutionCreatedEvent.now(
        task_execution_id=TaskExecutionId("task-abc"),
        task_execution_name=TaskExecutionName("my-task"),
        now=now,
    )


# ---------------------------------------------------------------------------
# Tests — DoD obligatory matrix
# ---------------------------------------------------------------------------


class TestBuildGraphExecutionOnTaskExecutionCreatedEventHandler:
    async def test_happy_path_builds_and_persists_graph_execution(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        logger: FakeLogger,
    ) -> None:
        await _seed_graph_definition(unit_of_work)
        handler = BuildGraphExecutionOnTaskExecutionCreatedEventHandler(
            unit_of_work, _InMemoryGraphDefinitionQueryService(unit_of_work), clock, id_generator, logger
        )

        await handler.handle(_task_created_event(clock.now()))

        graph_execution = await unit_of_work.repository(InMemoryGraphExecutionRepository).get_by_task_execution_id(
            TaskExecutionId("task-abc")
        )
        assert graph_execution is not None
        assert graph_execution.task_execution_id == TaskExecutionId("task-abc")
        assert graph_execution.initialization_status == GraphExecutionInitializationStatus.INITIALIZING
        assert len(graph_execution.graph_node_definition_execution_slots) == 2
        nodes = await unit_of_work.repository(InMemoryGraphNodeExecutionRepository).list_by_graph_execution_id(graph_execution.id)
        assert len(nodes) == 0
        assert any(isinstance(e, GraphExecutionInitializedEvent) for e in unit_of_work.committed_events)

    async def test_graph_definition_not_found_raises(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        logger: FakeLogger,
    ) -> None:
        # Use a fresh UoW without seeded graph_definition
        from shell.infrastructure.definition.persistence.memory import (
            InMemoryGraphDefinitionRepository,
        )

        fresh_unit_of_work = InMemoryUnitOfWork()
        fresh_unit_of_work._graph_definition_repository = InMemoryGraphDefinitionRepository()
        handler = BuildGraphExecutionOnTaskExecutionCreatedEventHandler(
            fresh_unit_of_work, _InMemoryGraphDefinitionQueryService(fresh_unit_of_work), clock, id_generator, logger
        )

        with pytest.raises(GraphDefinitionNotFoundException):
            await handler.handle(_task_created_event(clock.now()))

    async def test_idempotent_when_graph_already_exists(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        logger: FakeLogger,
    ) -> None:
        await _seed_graph_definition(unit_of_work)
        handler = BuildGraphExecutionOnTaskExecutionCreatedEventHandler(
            unit_of_work, _InMemoryGraphDefinitionQueryService(unit_of_work), clock, id_generator, logger
        )

        # First call builds the graph.
        await handler.handle(_task_created_event(clock.now()))
        first_graph = await unit_of_work.repository(InMemoryGraphExecutionRepository).get_by_task_execution_id(
            TaskExecutionId("task-abc")
        )
        assert first_graph is not None
        first_graph_execution_id = first_graph.id

        unit_of_work.committed_events.clear()
        # Second call must be a no-op.
        await handler.handle(_task_created_event(clock.now()))

        second_graph = await unit_of_work.repository(InMemoryGraphExecutionRepository).get_by_task_execution_id(
            TaskExecutionId("task-abc")
        )
        assert second_graph is not None
        assert second_graph.id == first_graph_execution_id
        assert unit_of_work.committed_events == []

    async def test_no_events_published_on_failure(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        logger: FakeLogger,
    ) -> None:
        # No graph_definition seeded — handler must NOT publish events when failing.
        from shell.infrastructure.definition.persistence.memory import (
            InMemoryGraphDefinitionRepository,
        )

        fresh_unit_of_work = InMemoryUnitOfWork()
        fresh_unit_of_work._graph_definition_repository = InMemoryGraphDefinitionRepository()
        handler = BuildGraphExecutionOnTaskExecutionCreatedEventHandler(
            fresh_unit_of_work, _InMemoryGraphDefinitionQueryService(fresh_unit_of_work), clock, id_generator, logger
        )

        with pytest.raises(GraphDefinitionNotFoundException):
            await handler.handle(_task_created_event(clock.now()))

        assert fresh_unit_of_work.committed_events == []
        # Graph must not exist either.
        assert (
            await fresh_unit_of_work.repository(InMemoryGraphExecutionRepository).get_by_task_execution_id(TaskExecutionId("task-abc"))
            is None
        )
