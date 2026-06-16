"""E2E test — Tasker full graph execution (Faza 14: step-by-step).

Uses InMemory adapters + FakeNodeProcessRunner so no real subprocess is spawned.
Verifies:
- ``RunTaskerWorkflowHandler`` creates a RUNNING Workflow and emits the first
  ``NodeExecutionRequested`` event.
- ``NodeExecutionWorker`` picks up the event, executes exactly one node, and
  emits the next ``NodeExecutionRequested`` until the graph is exhausted.
- ``NodeResult`` is persisted for every node (status = done/failed per runner).
- Workflow final status = ``done`` when all nodes succeed.
- Workflow final status = ``failed`` when any node fails (FailFastPolicy).
- ``WorkflowCompleted`` / ``NodeCompleted`` events are published.
"""
from __future__ import annotations

import pytest

from shell.application.bus.event_bus import EventBus
from shell.application.command_handlers.run_tasker_workflow_handler import (
    RunTaskerWorkflowHandler,
)
from shell.application.commands.commands import RunTaskerWorkflowCommand
from shell.application.event_handlers.node_execution_worker import NodeExecutionWorker
from shell.application.queries.queries import GetWorkflowQuery
from shell.application.query_handlers.query_handlers import GetWorkflowHandler
from shell.domain.entities.graph import Graph
from shell.domain.entities.graph_node import GraphNode
from shell.domain.entities.task import Task
from shell.domain.events.events import (
    NodeCompleted,
    NodeExecutionRequested,
    NodeFailed,
    WorkflowCompleted,
    WorkflowFailed,
)
from shell.domain.value_objects.ids import GraphId, NodeId, TaskId
from shell.domain.value_objects.mode import Mode
from shell.domain.value_objects.task_name import TaskName
from shell.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeLogger,
    FakeNodeProcessRunner,
    InMemoryQueryServices,
    InMemoryUnitOfWork,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_task_with_graph(task_id: str, node_modes: list[str], uow: InMemoryUnitOfWork) -> Task:
    """Build a Task and Graph with len(node_modes) nodes and store them via the UoW repos."""
    task_id = TaskId(task_id)
    task_name = TaskName(f"{task_id}-name")
    graph_id = GraphId.generate()

    nodes = [
        GraphNode(
            id=NodeId(f"{task_id}-node-{i}"),
            position=i,
            node_dir=f"/fake/{mode}-{i}",
            mode=Mode(mode),
            role=mode,
            node_type=mode,
        )
        for i, mode in enumerate(node_modes)
    ]

    from datetime import UTC, datetime

    from shell.domain.value_objects.hash import Hash
    from shell.domain.value_objects.ids import TemplateGraphId
    from shell.domain.value_objects.task_body import TaskBody
    from shell.domain.value_objects.version import Version

    task = Task(
        id=task_id,
        name=task_name,
        version=Version.initial(),
        hash=Hash.of("x"),
        body=TaskBody("# Task"),
        is_current=True,
        created_at=datetime.now(tz=UTC),
    )
    uow.tasks._store[task_id.value] = task

    graph = Graph(
        id=graph_id,
        task_id=task_id,
        template_graph_id=TemplateGraphId("template_graph_id"),
        raw_dict={},
        nodes=nodes,
    )
    uow.graphs._store[graph_id.value] = graph
    return task


async def _run_tasker_full(
    uow: InMemoryUnitOfWork,
    clock: FakeClock,
    id_gen: FakeIdGenerator,
    runner: FakeNodeProcessRunner,
    task_id: str,
    work_dir: str = "/tmp",
) -> tuple[str, list]:
    """Run the full tasker flow using InMemory UoW committed_events.

    Since we use pure Outbox pattern (no post-commit publisher), we manually
    dispatch committed events to the EventBus after each step to simulate
    the async Outbox → Inbox → EventBus relay.
    """
    event_bus = EventBus()

    worker = NodeExecutionWorker(
        uow=uow,
        clock=clock,
        id_gen=id_gen,
        runner=runner,
        logger=FakeLogger(),
    )
    event_bus.subscribe(NodeExecutionRequested, lambda: worker)

    handler = RunTaskerWorkflowHandler(
        uow=uow, clock=clock, id_gen=id_gen,
    )
    workflow_id = await handler.handle(
        RunTaskerWorkflowCommand(task_id=task_id, work_dir=work_dir)
    )

    processed_count = 0
    max_iterations = 10
    for _ in range(max_iterations):
        # Get new events since last processing
        new_events = uow.committed_events[processed_count:]
        if not new_events:
            break

        # Publish new events to EventBus
        for event in new_events:
            await event_bus.publish([event])

        processed_count = len(uow.committed_events)

        # Check if we have any unprocessed NodeExecutionRequested to continue
        # We need to check after publishing because worker may generate new ones
        pending = [e for e in uow.committed_events[processed_count:] if isinstance(e, NodeExecutionRequested)]
        if not pending and not any(isinstance(e, NodeExecutionRequested) for e in new_events):
            # No new NodeExecutionRequested generated in this iteration
            break

    # Collect all events for verification
    return workflow_id, list(uow.committed_events)


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
def queries(uow: InMemoryUnitOfWork) -> InMemoryQueryServices:
    """Fixture dostarczający serwis zapytań In-Memory dla testu E2E."""
    return InMemoryQueryServices(uow)


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
            queries: InMemoryQueryServices,
    ) -> None:
        runner = FakeNodeProcessRunner(stdout="ok", returncode=0)
        _make_task_with_graph("three-node-task", ["agent", "tool", "worker"], uow)

        workflow_id, _ = await _run_tasker_full(uow, clock, id_gen, runner, "three-node-task")
        dto = await GetWorkflowHandler(queries).handle(GetWorkflowQuery(workflow_id))
        assert dto is not None
        assert dto.status == "done"
        assert len(dto.node_states) ==3
        assert all(s.status == "done" for s in dto.node_states.values())

    async def test_three_node_results_saved(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
    ) -> None:
        runner = FakeNodeProcessRunner(stdout="result", returncode=0)
        _make_task_with_graph("nr-task", ["agent", "tool", "worker"], uow)

        workflow_id, _ = await _run_tasker_full(uow, clock, id_gen, runner, "nr-task")

        from shell.domain.value_objects.ids import WorkflowId
        wf = await uow.workflows.get_by_id(WorkflowId(workflow_id))
        assert wf is not None
        results = list(wf.node_results.values())
        assert len(results) == 3
        assert all(r.status.value == "done" for r in results)
        assert all(r.stdout == "result" for r in results)

    async def test_events_published(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
    ) -> None:
        runner = FakeNodeProcessRunner(returncode=0)
        _make_task_with_graph("ev-task", ["agent", "tool", "worker"], uow)

        _, events = await _run_tasker_full(uow, clock, id_gen, runner, "ev-task")

        types = [type(e) for e in events]
        assert WorkflowCompleted in types
        assert types.count(NodeCompleted) == 3
        assert NodeFailed not in types
        assert WorkflowFailed not in types


class TestRunTaskerWorkflowPartialFailure:
    """One node returns non-zero → workflow FAILED."""

    async def test_workflow_marked_failed(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            queries: InMemoryQueryServices,
    ) -> None:
        runner = FakeNodeProcessRunner(returncode=1, stderr="crash")
        _make_task_with_graph("fail-task", ["agent", "tool", "worker"], uow)

        workflow_id, _ = await _run_tasker_full(uow, clock, id_gen, runner, "fail-task")

        dto = await GetWorkflowHandler(queries).handle(GetWorkflowQuery(workflow_id))
        assert dto is not None
        assert dto.status == "failed"

    async def test_workflow_failed_event_published(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
    ) -> None:
        runner = FakeNodeProcessRunner(returncode=1)
        _make_task_with_graph("fail-ev-task", ["agent", "tool"], uow)

        _, events = await _run_tasker_full(uow, clock, id_gen, runner, "fail-ev-task")

        types = [type(e) for e in events]
        assert WorkflowFailed in types
        assert WorkflowCompleted not in types


class TestRunTaskerWorkflowEdgeCases:
    async def test_empty_graph_raises_workflow_has_no_nodes(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
    ) -> None:
        from shell.domain.exceptions import WorkflowHasNoNodes

        _make_task_with_graph("task-id-empty", [], uow)
        handler = RunTaskerWorkflowHandler(
            uow=uow, clock=clock, id_gen=id_gen,
        )
        with pytest.raises(WorkflowHasNoNodes):
            await handler.handle(
                RunTaskerWorkflowCommand(task_id="task-id-empty", work_dir="/tmp")
            )

    async def test_task_not_found_raises(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
    ) -> None:
        from shell.domain.exceptions import TaskNotFound

        handler = RunTaskerWorkflowHandler(uow=uow, clock=clock, id_gen=id_gen)
        with pytest.raises(TaskNotFound):
            await handler.handle(
                RunTaskerWorkflowCommand(task_id="task-id-ghost", work_dir="/tmp")
            )

