"""Unit tests for ``BuildGraphExecutionOnTaskExecutionCreatedEvent`` event handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from shell.application.execution.event_handlers.build_graph_execution_on_task_execution_created import (
    BuildGraphExecutionOnTaskExecutionCreatedEvent,
)
from shell.application.platform.exceptions import GraphDefinitionNotFoundException
from shell.domain.definition.entities.graph_definition import GraphDefinition
from shell.domain.definition.entities.graph_node_definition import GraphNodeDefinition
from shell.domain.definition.value_objects.ids import GraphDefinitionId, GraphNodeDefinitionId
from shell.domain.execution.events import GraphExecutionBuiltEvent, TaskExecutionCreatedEvent
from shell.domain.execution.value_objects.graph_execution_definition import (
    GraphExecutionDefinition,
    GraphNodeExecutionDefinition,
)
from shell.domain.execution.value_objects.ids import TaskExecutionId
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.platform.value_objects.mode import Mode
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeIdGenerator,
    FakeLogger,
    InMemoryUnitOfWork,
)

if TYPE_CHECKING:
    from datetime import datetime


class _InMemoryGraphDefinitionQueryService:
    def __init__(self, uow: InMemoryUnitOfWork) -> None:
        self._repo = uow.graph_definitions

    async def get_graph_definition_by_name(self, name: str) -> GraphExecutionDefinition | None:

        entity = await self._repo.get_graph_definition_by_name(name)
        if entity is None:
            return None
        return self._to_dto(entity)

    async def get_graph_definition(self, definition_id: str) -> GraphExecutionDefinition | None:
        from shell.domain.definition.value_objects.ids import GraphDefinitionId

        entity = await self._repo.get_by_id(GraphDefinitionId(definition_id))
        if entity is None:
            return None
        return self._to_dto(entity)

    def _to_dto(self, entity: object) -> GraphExecutionDefinition:

        graph_definition: GraphDefinition = entity  # type: ignore[assignment]
        return GraphExecutionDefinition(
            id=graph_definition.id.value
            if hasattr(graph_definition.id, "value")
            else str(graph_definition.id),
            name=graph_definition.name,
            graph_node_execution_definitions=[
                GraphNodeExecutionDefinition(
                    position=graph_node_definition.position,
                    mode=graph_node_definition.mode.value
                    if hasattr(graph_node_definition.mode, "value")
                    else str(graph_node_definition.mode),
                    role=graph_node_definition.role,
                    node_type=graph_node_definition.node_type,
                    model=graph_node_definition.model,
                    command=graph_node_definition.command,
                    timeout=graph_node_definition.timeout,
                    retries=graph_node_definition.retries,
                    log_level=graph_node_definition.log_level,
                    max_step=graph_node_definition.max_step,
                    no_ask_user=graph_node_definition.no_ask_user,
                    autopilot=graph_node_definition.autopilot,
                    status_initial=graph_node_definition.status_initial,
                    script=getattr(graph_node_definition, "script", ""),
                    script_type=getattr(graph_node_definition, "script_type", ""),
                )
                for graph_node_definition in graph_definition.graph_node_definitions
            ],
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def uow() -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork()


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture()
def id_gen() -> FakeIdGenerator:
    return FakeIdGenerator()


@pytest.fixture()
def logger() -> FakeLogger:
    return FakeLogger()


async def _seed_graph_definition(
    uow: InMemoryUnitOfWork, name: str = "base_planner"
) -> GraphDefinition:
    graph_definition = GraphDefinition(
        id=GraphDefinitionId(f"{name}-id"),
        name=name,
        purpose="planning",
        graph_node_definitions=[
            GraphNodeDefinition(
                id=GraphNodeDefinitionId("tn-1"),
                position=0,
                mode=Mode("agent"),
                role="agent",
                node_type="agent",
            ),
            GraphNodeDefinition(
                id=GraphNodeDefinitionId("tn-2"),
                position=1,
                mode=Mode("worker"),
                role="worker",
                node_type="worker",
            ),
        ],
    )
    # Clear any existing graph_definition with the same name (constructor seeds one)
    repo = uow.graph_definitions
    keys_to_remove = [k for k, v in repo._store.items() if v.name == name]
    for k in keys_to_remove:
        del repo._store[k]
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


class TestBuildGraphExecutionOnTaskExecutionCreatedEvent:
    async def test_happy_path_builds_and_persists_graph_execution(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        logger: FakeLogger,
    ) -> None:
        await _seed_graph_definition(uow)
        handler = BuildGraphExecutionOnTaskExecutionCreatedEvent(
            uow, _InMemoryGraphDefinitionQueryService(uow), clock, id_gen, logger
        )

        await handler.handle(_task_created_event(clock.now()))

        graph_execution = await uow.graph_executions.get_by_task_execution_id(
            TaskExecutionId("task-abc")
        )
        assert graph_execution is not None
        assert graph_execution.task_execution_id == TaskExecutionId("task-abc")
        assert len(graph_execution.graph_node_executions) == 2
        assert any(isinstance(e, GraphExecutionBuiltEvent) for e in uow.committed_events)

    async def test_graph_definition_not_found_raises(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        logger: FakeLogger,
    ) -> None:
        # Use a fresh UoW without seeded graph_definition
        from shell.infrastructure.definition.persistence.memory import (
            InMemoryGraphDefinitionRepository,
        )

        fresh_uow = InMemoryUnitOfWork()
        fresh_uow._graph_definitions = InMemoryGraphDefinitionRepository()
        handler = BuildGraphExecutionOnTaskExecutionCreatedEvent(
            fresh_uow, _InMemoryGraphDefinitionQueryService(fresh_uow), clock, id_gen, logger
        )

        with pytest.raises(GraphDefinitionNotFoundException):
            await handler.handle(_task_created_event(clock.now()))

    async def test_idempotent_when_graph_already_exists(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        logger: FakeLogger,
    ) -> None:
        await _seed_graph_definition(uow)
        handler = BuildGraphExecutionOnTaskExecutionCreatedEvent(
            uow, _InMemoryGraphDefinitionQueryService(uow), clock, id_gen, logger
        )

        # First call builds the graph.
        await handler.handle(_task_created_event(clock.now()))
        first_graph = await uow.graph_executions.get_by_task_execution_id(
            TaskExecutionId("task-abc")
        )
        assert first_graph is not None
        first_graph_execution_id = first_graph.id

        uow.committed_events.clear()
        # Second call must be a no-op.
        await handler.handle(_task_created_event(clock.now()))

        second_graph = await uow.graph_executions.get_by_task_execution_id(
            TaskExecutionId("task-abc")
        )
        assert second_graph is not None
        assert second_graph.id == first_graph_execution_id
        assert uow.committed_events == []

    async def test_no_events_published_on_failure(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        logger: FakeLogger,
    ) -> None:
        # No graph_definition seeded — handler must NOT publish events when failing.
        from shell.infrastructure.definition.persistence.memory import (
            InMemoryGraphDefinitionRepository,
        )

        fresh_uow = InMemoryUnitOfWork()
        fresh_uow._graph_definitions = InMemoryGraphDefinitionRepository()
        handler = BuildGraphExecutionOnTaskExecutionCreatedEvent(
            fresh_uow, _InMemoryGraphDefinitionQueryService(fresh_uow), clock, id_gen, logger
        )

        with pytest.raises(GraphDefinitionNotFoundException):
            await handler.handle(_task_created_event(clock.now()))

        assert fresh_uow.committed_events == []
        # Graph must not exist either.
        assert (
            await fresh_uow.graph_executions.get_by_task_execution_id(TaskExecutionId("task-abc"))
            is None
        )
