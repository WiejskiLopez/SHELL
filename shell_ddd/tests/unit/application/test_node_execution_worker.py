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

from shell_ddd.application.event_handlers.node_execution_worker import NodeExecutionWorker
from shell_ddd.domain.entities.graph import Graph
from shell_ddd.domain.entities.graph_node import GraphNode
from shell_ddd.domain.entities.task import Task
from shell_ddd.domain.entities.workflow import Workflow
from shell_ddd.domain.events.events import (
    NodeAdvanced,
    NodeCompleted,
    NodeExecutionRequested,
    NodeFailed,
    WorkflowCompleted,
    WorkflowFailed,
)
from shell_ddd.domain.value_objects.hash import Hash
from shell_ddd.domain.value_objects.ids import (
    GraphId,
    NodeId,
    TaskId,
    TemplateGraphId,
    WorkflowId,
)
from shell_ddd.domain.value_objects.mode import Mode
from shell_ddd.domain.value_objects.status import Status
from shell_ddd.domain.value_objects.task_body import TaskBody
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.domain.value_objects.version import Version
from shell_ddd.domain.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)
from shell_ddd.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeLogger,
    FakeNodeProcessRunner,
    InMemoryUnitOfWork,
)

_NOW = datetime(2026, 6, 1, tzinfo=UTC)


def _build_graph(uow: InMemoryUnitOfWork, task_name: str, modes: list[str]) -> tuple[Task, Graph]:
    task = Task(
        id=TaskId.generate(),
        name=TaskName(task_name),
        version=Version.initial(),
        hash=Hash.of("x"),
        body=TaskBody("# Task"),
        is_current=True,
        created_at=_NOW,
    )
    uow.tasks._store[task.id.value] = task

    nodes = [
        GraphNode(
            id=NodeId(f"{task_name}-n{i}"),
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
        task_id=task.id,
        template_graph_id=TemplateGraphId("tpl"),
        raw_dict={},
        nodes=nodes,
    )
    uow.graphs._store[graph.id.value] = graph
    return task, graph


async def _persist_running_workflow(
    uow: InMemoryUnitOfWork, task_name: str, first_node: NodeId
) -> Workflow:
    wf = Workflow.new(id_=WorkflowId.generate(), task_name=task_name, now=_NOW)
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
        publisher = FakeEventPublisher()
        uow = InMemoryUnitOfWork(post_commit_publisher=publisher)
        task, graph = _build_graph(uow, "happy", ["agent", "tool"])
        wf = await _persist_running_workflow(uow, task.name.value, graph.nodes[0].id)

        runner = FakeNodeProcessRunner(stdout="ok", returncode=0)
        worker = _make_worker(uow, runner)

        await worker.handle(
            NodeExecutionRequested.now(wf.id, graph.nodes[0].id, now=_NOW)
        )

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.running()
        assert stored.cursor.current_node_id == graph.nodes[1].id

        types = [type(e) for e in publisher.published]
        assert NodeCompleted in types
        assert NodeAdvanced in types
        assert NodeExecutionRequested in types

    async def test_last_node_success_finishes_workflow(self) -> None:
        publisher = FakeEventPublisher()
        uow = InMemoryUnitOfWork(post_commit_publisher=publisher)
        task, graph = _build_graph(uow, "single", ["agent"])
        wf = await _persist_running_workflow(uow, task.name.value, graph.nodes[0].id)

        runner = FakeNodeProcessRunner(returncode=0)
        worker = _make_worker(uow, runner)

        await worker.handle(
            NodeExecutionRequested.now(wf.id, graph.nodes[0].id, now=_NOW)
        )

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.done()
        assert stored.cursor.current_node_id is None

        types = [type(e) for e in publisher.published]
        assert WorkflowCompleted in types


class TestNodeExecutionWorkerFailure:
    async def test_node_failure_aborts_under_fail_fast_policy(self) -> None:
        publisher = FakeEventPublisher()
        uow = InMemoryUnitOfWork(post_commit_publisher=publisher)
        task, graph = _build_graph(uow, "fail", ["agent", "tool"])
        wf = await _persist_running_workflow(uow, task.name.value, graph.nodes[0].id)

        runner = FakeNodeProcessRunner(returncode=1, stderr="boom")
        worker = _make_worker(uow, runner)

        await worker.handle(
            NodeExecutionRequested.now(wf.id, graph.nodes[0].id, now=_NOW)
        )

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.failed()
        assert stored.cursor.current_node_id is None

        types = [type(e) for e in publisher.published]
        assert NodeFailed in types
        assert WorkflowFailed in types
        # Crucially — no advance, no further work requested.
        assert NodeAdvanced not in types
        assert NodeExecutionRequested not in types


class TestNodeExecutionWorkerIdempotency:
    async def test_stale_cursor_event_is_dropped(self) -> None:
        publisher = FakeEventPublisher()
        uow = InMemoryUnitOfWork(post_commit_publisher=publisher)
        task, graph = _build_graph(uow, "stale", ["agent", "tool"])
        wf = await _persist_running_workflow(uow, task.name.value, graph.nodes[0].id)

        runner = FakeNodeProcessRunner(returncode=0)
        worker = _make_worker(uow, runner)

        # Worker is asked to process node[1] but the cursor still points at node[0].
        await worker.handle(
            NodeExecutionRequested.now(wf.id, graph.nodes[1].id, now=_NOW)
        )

        # Workflow state must be unchanged.
        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.running()
        assert stored.cursor.current_node_id == graph.nodes[0].id
        # Runner was not called (early return).
        assert runner.calls == []
        # No domain events were published.
        assert publisher.published == []

    async def test_terminal_workflow_ignores_event(self) -> None:
        publisher = FakeEventPublisher()
        uow = InMemoryUnitOfWork(post_commit_publisher=publisher)
        task, graph = _build_graph(uow, "terminal", ["agent"])
        wf = await _persist_running_workflow(uow, task.name.value, graph.nodes[0].id)

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

        await worker.handle(
            NodeExecutionRequested.now(wf.id, graph.nodes[0].id, now=_NOW)
        )

        # Worker should silently ignore the re-delivery.
        assert runner.calls == []
        assert publisher.published == []
