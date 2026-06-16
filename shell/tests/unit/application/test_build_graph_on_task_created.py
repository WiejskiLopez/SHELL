"""Unit tests for ``BuildGraphOnTaskCreated`` event handler."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shell.application.event_handlers.build_graph_on_task_created import (
    BuildGraphOnTaskCreated,
)
from shell.application.exceptions import TemplateGraphNotFoundException
from shell.domain.entities.template_graph import TemplateGraph
from shell.domain.entities.template_graph_node import TemplateGraphNode
from shell.domain.events.events import GraphBuilt, TaskCreated
from shell.domain.value_objects.ids import (
    TaskId,
    TemplateGraphId,
    TemplateGraphNodeId,
)
from shell.domain.value_objects.mode import Mode
from shell.domain.value_objects.task_name import TaskName
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


def _seed_template(uow: InMemoryUnitOfWork, name: str = "base_planner") -> TemplateGraph:
    template = TemplateGraph(
        id=TemplateGraphId(f"{name}-id"),
        name=name,
        purpose="planning",
        nodes=[
            TemplateGraphNode(
                id=TemplateGraphNodeId("tn-1"),
                position=0,
                mode=Mode("agent"),
                role="agent",
                node_type="agent",
            ),
            TemplateGraphNode(
                id=TemplateGraphNodeId("tn-2"),
                position=1,
                mode=Mode("worker"),
                role="worker",
                node_type="worker",
            ),
        ],
    )
    uow.template_graphs._store[name] = template
    return template


def _task_created_event(now: datetime) -> TaskCreated:
    return TaskCreated.now(
        task_id=TaskId("task-abc"),
        task_name=TaskName("my-task"),
        now=now,
    )


# ---------------------------------------------------------------------------
# Tests — DoD obligatory matrix
# ---------------------------------------------------------------------------


class TestBuildGraphOnTaskCreated:
    async def test_happy_path_builds_and_persists_graph(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        logger: FakeLogger,
    ) -> None:
        _seed_template(uow)
        handler = BuildGraphOnTaskCreated(uow, clock, id_gen, logger)

        await handler.handle(_task_created_event(clock.now()))

        graph = await uow.graphs.get_by_task_id(TaskId("task-abc"))
        assert graph is not None
        assert graph.task_id == TaskId("task-abc")
        assert len(graph.nodes) == 2
        assert any(isinstance(e, GraphBuilt) for e in uow.committed_events)

    async def test_template_not_found_raises(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        logger: FakeLogger,
    ) -> None:
        # Replace seeded base_planner with nothing
        uow.template_graphs._store.clear()
        handler = BuildGraphOnTaskCreated(uow, clock, id_gen, logger)

        with pytest.raises(TemplateGraphNotFoundException):
            await handler.handle(_task_created_event(clock.now()))

    async def test_idempotent_when_graph_already_exists(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        logger: FakeLogger,
    ) -> None:
        _seed_template(uow)
        handler = BuildGraphOnTaskCreated(uow, clock, id_gen, logger)

        # First call builds the graph.
        await handler.handle(_task_created_event(clock.now()))
        first_graph = await uow.graphs.get_by_task_id(TaskId("task-abc"))
        assert first_graph is not None
        first_graph_id = first_graph.id

        uow.committed_events.clear()
        # Second call must be a no-op.
        await handler.handle(_task_created_event(clock.now()))

        second_graph = await uow.graphs.get_by_task_id(TaskId("task-abc"))
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
        # No template seeded — handler must NOT publish events when failing.
        uow.template_graphs._store.clear()
        handler = BuildGraphOnTaskCreated(uow, clock, id_gen, logger)

        with pytest.raises(TemplateGraphNotFoundException):
            await handler.handle(_task_created_event(clock.now()))

        assert uow.committed_events == []
        # Graph must not exist either.
        assert await uow.graphs.get_by_task_id(TaskId("task-abc")) is None
