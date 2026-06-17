"""Unit tests for ``NodeExecutionWorker`` (Process Manager / Saga step).

The worker subscribes to ``NodeExecutionRequested`` and processes exactly one
node per invocation. These tests verify:

* Happy path — node succeeds, cursor advances, next ``NodeExecutionRequested`` emitted.
* Last-node success — workflow transitions to ``done``.
* Node failure under ``FailFastPolicy`` — workflow transitions to ``failed``.
* Stale-cursor idempotency — events for a node the cursor no longer points at are dropped.
* Terminal-status idempotency — events delivered after ``done``/``failed`` are dropped.
"""

from __future__ import annotations

from datetime import UTC, datetime

from shell.application.event_handlers.node_execution_worker import NodeExecutionWorker
from shell.domain.entities.graph import Graph
from shell.domain.entities.graph_node import GraphNode
from shell.domain.entities.task_execution import TaskExecution
from shell.domain.entities.workflow import Workflow
from shell.domain.events.events import (
    NodeAdvanced,
    NodeCompleted,
    NodeExecutionRequested,
    NodeFailed,
    WorkflowCompleted,
    WorkflowFailed,
)
from shell.domain.value_objects.hash import Hash
from shell.domain.value_objects.ids import (
    GraphDefinitionId,
    GraphId,
    NodeId,
    TaskExecutionId,
    WorkflowId,
)
from shell.domain.value_objects.mode import Mode
from shell.domain.value_objects.status import Status
from shell.domain.value_objects.task_execution_body import TaskExecutionBody
from shell.domain.value_objects.task_execution_name import TaskExecutionName
from shell.domain.value_objects.version import Version
from shell.domain.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)
from shell.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeIdGenerator,
    FakeLogger,
    FakeNodeProcessRunner,
    InMemoryUnitOfWork,
)

_NOW = datetime(2026, 6, 1, tzinfo=UTC)


def _build_graph(uow: InMemoryUnitOfWork, task_execution_name: str, modes: list[str]) -> tuple[TaskExecution, Graph]:
    task_execution = TaskExecution(
        id=TaskExecutionId.generate(),
        name=TaskExecutionName(task_execution_name),
        version=Version.initial(),
        hash=Hash.of("x"),
        body=TaskExecutionBody("# Task"),
        is_current=True,
        created_at=_NOW,
    )
    uow.task_executions._store[task_execution.id.value] = task_execution  # type: ignore[attr-defined]

    nodes = [
        GraphNode(
            id=NodeId(f"{task_execution.id.value}-n{i}"),
            position=i,
            node_dir=f"/fake/{m}-{i}",
            mode=Mode(m),
            role=m,
            node_type=m,
        )
        for i, m in enumerate(modes)
    ]
    graph = Graph(
        id=GraphId.generate(),
        task_execution_id=task_execution.id,
        graph_definition_id=GraphDefinitionId("tpl"),
        nodes=nodes,
    )
    uow.graphs._store[graph.id.value] = graph  # type: ignore[attr-defined]
    return task_execution, graph


async def _persist_running_workflow(
    uow: InMemoryUnitOfWork, task_execution_id: TaskExecutionId, first_node: NodeId
) -> Workflow:
    wf = Workflow.new(id_=WorkflowId.generate(), task_execution_id=task_execution_id, now=_NOW)
    wf.start_at(
        first_node_id=first_node,
        context=WorkflowExecutionContext(work_dir="/tmp", correlation_id="cid"),
        now=_NOW,
    )
    async with uow:
        await uow.workflows.save(wf)
        await uow.commit()
    return wf


def _make_worker(
    uow: InMemoryUnitOfWork,
    runner: FakeNodeProcessRunner,
) -> NodeExecutionWorker:
    return NodeExecutionWorker(
        uow=uow,
        clock=FakeClock(_NOW),
        id_gen=FakeIdGenerator(),
        runner=runner,
        logger=FakeLogger(),
    )


class TestNodeExecutionWorkerHappyPath:
    async def test_first_node_success_advances_to_second(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph = _build_graph(uow, "happy", ["agent", "tool"])
        wf = await _persist_running_workflow(uow, task_execution.id, graph.nodes[0].id)

        runner = FakeNodeProcessRunner(stdout="ok", returncode=0)
        worker = _make_worker(uow, runner)

        await worker.handle(NodeExecutionRequested.now(wf.id, graph.nodes[0].id, now=_NOW))

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.running()
        assert stored.cursor.current_node_id == graph.nodes[1].id

        types = [type(e) for e in uow.committed_events]
        assert NodeCompleted in types
        assert NodeAdvanced in types
        assert NodeExecutionRequested in types

    async def test_last_node_success_finishes_workflow(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph = _build_graph(uow, "single", ["agent"])
        wf = await _persist_running_workflow(uow, task_execution.id, graph.nodes[0].id)

        runner = FakeNodeProcessRunner(returncode=0)
        worker = _make_worker(uow, runner)

        await worker.handle(NodeExecutionRequested.now(wf.id, graph.nodes[0].id, now=_NOW))

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.done()
        assert stored.cursor.current_node_id is None

        types = [type(e) for e in uow.committed_events]
        assert WorkflowCompleted in types


class TestNodeExecutionWorkerFailure:
    async def test_node_failure_aborts_under_fail_fast_policy(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph = _build_graph(uow, "fail", ["agent", "tool"])
        wf = await _persist_running_workflow(uow, task_execution.id, graph.nodes[0].id)

        runner = FakeNodeProcessRunner(returncode=1, stderr="boom")
        worker = _make_worker(uow, runner)

        await worker.handle(NodeExecutionRequested.now(wf.id, graph.nodes[0].id, now=_NOW))

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.failed()
        assert stored.cursor.current_node_id is None

        types = [type(e) for e in uow.committed_events]
        assert NodeFailed in types
        assert WorkflowFailed in types
        # Crucially — no advance, no further work requested.
        assert NodeAdvanced not in types
        assert NodeExecutionRequested not in types


class TestNodeExecutionWorkerIdempotency:
    async def test_stale_cursor_event_is_dropped(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph = _build_graph(uow, "stale", ["agent", "tool"])
        wf = await _persist_running_workflow(uow, task_execution.id, graph.nodes[0].id)

        runner = FakeNodeProcessRunner(returncode=0)
        worker = _make_worker(uow, runner)

        # Worker is asked to process node[1] but the cursor still points at node[0].
        await worker.handle(NodeExecutionRequested.now(wf.id, graph.nodes[1].id, now=_NOW))

        # Workflow state must be unchanged.
        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.running()
        assert stored.cursor.current_node_id == graph.nodes[0].id
        # Runner was not called (early return).
        assert runner.calls == []
        # No domain events were published.
        assert uow.committed_events == []

    async def test_terminal_workflow_ignores_event(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph = _build_graph(uow, "terminal", ["agent"])
        wf = await _persist_running_workflow(uow, task_execution.id, graph.nodes[0].id)

        # Force the workflow into ``done`` state directly.
        wf.record_node_result(
            result_id=FakeIdGenerator().new_node_result_id(),
            node_id=graph.nodes[0].id,
            status=Status.done(),
            now=_NOW,
        )
        wf.finish(_NOW)
        async with uow:
            await uow.workflows.save(wf)
            await uow.commit()

        runner = FakeNodeProcessRunner(returncode=0)
        worker = _make_worker(uow, runner)

        await worker.handle(NodeExecutionRequested.now(wf.id, graph.nodes[0].id, now=_NOW))

        # Worker should silently ignore the re-delivery.
        assert runner.calls == []
        assert uow.committed_events == []
