"""Unit tests for ``BuildGraphOnTaskExecutionCreated`` event handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shell.application.event_handlers.build_graph_on_task_execution_created import (
    BuildGraphOnTaskExecutionCreated,
)
from shell.application.exceptions import GraphDefinitionNotFoundException
from shell.domain.entities.graph_definition import GraphDefinition
from shell.domain.entities.graph_definition_node import GraphDefinitionNode
from shell.domain.events.events import GraphBuilt, TaskExecutionCreated
from shell.domain.value_objects.ids import (
    GraphDefinitionId,
    GraphDefinitionNodeId,
    TaskExecutionId,
)
from shell.domain.value_objects.mode import Mode
from shell.domain.value_objects.task_execution_name import TaskExecutionName
from shell.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeIdGenerator,
    FakeLogger,
    InMemoryUnitOfWork,
)

if TYPE_CHECKING:
    from datetime import datetime

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


async def _seed_graph_definition(uow: InMemoryUnitOfWork, name: str = "base_planner") -> GraphDefinition:
    graph_definition = GraphDefinition(
        id=GraphDefinitionId(f"{name}-id"),
        name=name,
        purpose="planning",
        nodes=[
            GraphDefinitionNode(
                id=GraphDefinitionNodeId("tn-1"),
                position=0,
                mode=Mode("agent"),
                role="agent",
                node_type="agent",
            ),
            GraphDefinitionNode(
                id=GraphDefinitionNodeId("tn-2"),
                position=1,
                mode=Mode("worker"),
                role="worker",
                node_type="worker",
            ),
        ],
    )
    # Clear any existing graph_definition with the same name (constructor seeds one)
    repo = uow.graph_definitions
    keys_to_remove = [k for k, v in repo._store.items() if v.name == name]  # type: ignore[attr-defined]
    for k in keys_to_remove:
        del repo._store[k]  # type: ignore[attr-defined]
    await repo.save(graph_definition)
    return graph_definition


def _task_created_event(now: datetime) -> TaskExecutionCreated:
    return TaskExecutionCreated.now(
        task_execution_id=TaskExecutionId("task-abc"),
        task_execution_name=TaskExecutionName("my-task"),
        now=now,
    )


# ---------------------------------------------------------------------------
# Tests — DoD obligatory matrix
# ---------------------------------------------------------------------------


class TestBuildGraphOnTaskExecutionCreated:
    async def test_happy_path_builds_and_persists_graph(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        logger: FakeLogger,
    ) -> None:
        await _seed_graph_definition(uow)
        handler = BuildGraphOnTaskExecutionCreated(uow, clock, id_gen, logger)

        await handler.handle(_task_created_event(clock.now()))

        graph = await uow.graphs.get_by_task_execution_id(TaskExecutionId("task-abc"))
        assert graph is not None
        assert graph.task_execution_id == TaskExecutionId("task-abc")
        assert len(graph.nodes) == 2
        assert any(isinstance(e, GraphBuilt) for e in uow.committed_events)

    async def test_graph_definition_not_found_raises(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        logger: FakeLogger,
    ) -> None:
        # Use a fresh UoW without seeded graph_definition
        from shell.infrastructure.persistence.memory.memory import InMemoryGraphDefinitionRepository

        fresh_uow = InMemoryUnitOfWork()
        fresh_uow._graph_definitions = InMemoryGraphDefinitionRepository()
        handler = BuildGraphOnTaskExecutionCreated(fresh_uow, clock, id_gen, logger)

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
        handler = BuildGraphOnTaskExecutionCreated(uow, clock, id_gen, logger)

        # First call builds the graph.
        await handler.handle(_task_created_event(clock.now()))
        first_graph = await uow.graphs.get_by_task_execution_id(TaskExecutionId("task-abc"))
        assert first_graph is not None
        first_graph_id = first_graph.id

        uow.committed_events.clear()
        # Second call must be a no-op.
        await handler.handle(_task_created_event(clock.now()))

        second_graph = await uow.graphs.get_by_task_execution_id(TaskExecutionId("task-abc"))
        assert second_graph is not None
        assert second_graph.id == first_graph_id
        assert uow.committed_events == []

    async def test_no_events_published_on_failure(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        logger: FakeLogger,
    ) -> None:
        # No graph_definition seeded — handler must NOT publish events when failing.
        from shell.infrastructure.persistence.memory.memory import InMemoryGraphDefinitionRepository

        fresh_uow = InMemoryUnitOfWork()
        fresh_uow._graph_definitions = InMemoryGraphDefinitionRepository()
        handler = BuildGraphOnTaskExecutionCreated(fresh_uow, clock, id_gen, logger)

        with pytest.raises(GraphDefinitionNotFoundException):
            await handler.handle(_task_created_event(clock.now()))

        assert fresh_uow.committed_events == []
        # Graph must not exist either.
        assert await fresh_uow.graphs.get_by_task_execution_id(TaskExecutionId("task-abc")) is None
