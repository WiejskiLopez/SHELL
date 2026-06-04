"""E2E test — Tasker full graph execution (Faza 10).

Uses InMemory adapters + FakeNodeProcessRunner so no real subprocess is spawned.
Verifies:
- RunTaskerWorkflowHandler creates a Workflow and runs all 3 graph nodes.
- NodeResult is persisted for every node (status = done/failed per runner config).
- Workflow final status = COMPLETED when all nodes succeed.
- Workflow final status = FAILED when any node fails.
- WorkflowCompleted / NodeCompleted events are published.
"""
from __future__ import annotations

import pytest

from shell_ddd.application.command_handlers.run_tasker_workflow_handler import RunTaskerWorkflowHandler
from shell_ddd.application.commands.commands import RunTaskerWorkflowCommand
from shell_ddd.application.queries.queries import GetWorkflowQuery
from shell_ddd.application.query_handlers.query_handlers import GetWorkflowHandler
from shell_ddd.domain.entities.task import Graph, GraphNode, Task
from shell_ddd.domain.events.events import NodeCompleted, NodeFailed, WorkflowCompleted, WorkflowFailed
from shell_ddd.domain.value_objects.ids import GraphId, NodeId, TaskId
from shell_ddd.domain.value_objects.mode import Mode
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeNodeProcessRunner,
    InMemoryUnitOfWork,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_task_with_graph(name: str, node_modes: list[str], uow_tasks_store: dict) -> Task:
    """Build a Task with a Graph containing len(node_modes) nodes and store it in place."""
    task_id = TaskId.generate()
    task_name = TaskName(name)
    graph_id = GraphId.generate()

    nodes = [
        GraphNode(
            id=NodeId(f"{name}-node-{i}"),
            position=i,
            node_dir=f"/fake/{mode}-{i}",
            mode=Mode(mode),
            role=mode,
            node_type=mode,
        )
        for i, mode in enumerate(node_modes)
    ]

    from datetime import UTC, datetime

    task = Task(
        id=task_id,
        name=task_name,
        version=1,
        hash=__import__("shell_ddd.domain.value_objects.hash", fromlist=["Hash"]).Hash.of("x"),
        body_md="# Task",
        body_yaml_raw="",
        is_current=True,
        created_at=datetime.now(tz=UTC),
        graph=Graph(
            id=graph_id,
            task_id=task_id,
            raw_dict={},
            nodes=nodes,
        ),
    )
    uow_tasks_store[task_id.value] = task
    return task


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
def events() -> FakeEventPublisher:
    return FakeEventPublisher()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRunTaskerWorkflowHappyPath:
    """All 3 nodes succeed → workflow COMPLETED."""

    async def test_all_nodes_complete(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
    ) -> None:
        runner = FakeNodeProcessRunner(stdout="ok", returncode=0)
        _make_task_with_graph(
            "three-node-task",
            ["agent", "tool", "worker"],
            uow.tasks._store,
        )

        handler = RunTaskerWorkflowHandler(uow, clock, id_gen, runner, events)
        workflow_id = await handler.handle(
            RunTaskerWorkflowCommand(task_name="three-node-task", work_dir="/tmp")
        )

        # Workflow persisted and marked complete
        dto = await GetWorkflowHandler(uow).handle(GetWorkflowQuery(workflow_id))
        assert dto is not None
        assert dto.status == "done"
        assert len(dto.node_states) == 3
        assert all(s.status == "done" for s in dto.node_states.values())

    async def test_three_node_results_saved(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
    ) -> None:
        runner = FakeNodeProcessRunner(stdout="result", returncode=0)
        _make_task_with_graph("nr-task", ["agent", "tool", "worker"], uow.tasks._store)

        handler = RunTaskerWorkflowHandler(uow, clock, id_gen, runner, events)
        await handler.handle(RunTaskerWorkflowCommand(task_name="nr-task", work_dir="/tmp"))

        results = list(uow.node_results._store.values())
        assert len(results) == 3
        assert all(r.status.value == "done" for r in results)
        assert all(r.stdout == "result" for r in results)

    async def test_events_published(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
    ) -> None:
        runner = FakeNodeProcessRunner(returncode=0)
        _make_task_with_graph("ev-task", ["agent", "tool", "worker"], uow.tasks._store)

        handler = RunTaskerWorkflowHandler(uow, clock, id_gen, runner, events)
        await handler.handle(RunTaskerWorkflowCommand(task_name="ev-task", work_dir="/tmp"))

        types = [type(e) for e in events.published]
        assert WorkflowCompleted in types
        assert types.count(NodeCompleted) == 3
        # No failures
        assert NodeFailed not in types
        assert WorkflowFailed not in types


class TestRunTaskerWorkflowPartialFailure:
    """One node returns non-zero → workflow FAILED."""

    async def test_workflow_marked_failed(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
    ) -> None:
        runner = FakeNodeProcessRunner(returncode=1, stderr="crash")
        _make_task_with_graph(
            "fail-task",
            ["agent", "tool", "worker"],
            uow.tasks._store,
        )

        handler = RunTaskerWorkflowHandler(uow, clock, id_gen, runner, events)
        workflow_id = await handler.handle(
            RunTaskerWorkflowCommand(task_name="fail-task", work_dir="/tmp")
        )

        dto = await GetWorkflowHandler(uow).handle(GetWorkflowQuery(workflow_id))
        assert dto is not None
        assert dto.status == "failed"

    async def test_workflow_failed_event_published(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
    ) -> None:
        runner = FakeNodeProcessRunner(returncode=1)
        _make_task_with_graph("fail-ev-task", ["agent", "tool"], uow.tasks._store)

        handler = RunTaskerWorkflowHandler(uow, clock, id_gen, runner, events)
        await handler.handle(RunTaskerWorkflowCommand(task_name="fail-ev-task", work_dir="/tmp"))

        types = [type(e) for e in events.published]
        assert WorkflowFailed in types
        assert WorkflowCompleted not in types


class TestRunTaskerWorkflowEdgeCases:
    async def test_empty_graph_creates_completed_workflow(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
    ) -> None:
        runner = FakeNodeProcessRunner(returncode=0)
        _make_task_with_graph("empty-task", [], uow.tasks._store)

        handler = RunTaskerWorkflowHandler(uow, clock, id_gen, runner, events)
        workflow_id = await handler.handle(
            RunTaskerWorkflowCommand(task_name="empty-task", work_dir="/tmp")
        )

        dto = await GetWorkflowHandler(uow).handle(GetWorkflowQuery(workflow_id))
        assert dto is not None
        assert dto.status == "done"

    async def test_task_not_found_raises(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
    ) -> None:
        from shell_ddd.domain.exceptions import TaskNotFound

        runner = FakeNodeProcessRunner(returncode=0)
        handler = RunTaskerWorkflowHandler(uow, clock, id_gen, runner, events)
        with pytest.raises(TaskNotFound):
            await handler.handle(
                RunTaskerWorkflowCommand(task_name="ghost-task", work_dir="/tmp")
            )
