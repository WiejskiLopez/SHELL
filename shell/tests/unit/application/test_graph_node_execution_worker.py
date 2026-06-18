"""Unit tests for ``GraphNodeExecutionWorker`` (Process Manager / Saga step).

The worker subscribes to ``GraphNodeExecutionRequested`` and processes exactly one
node per invocation. These tests verify:

* Happy path — node succeeds, cursor advances, next ``GraphNodeExecutionRequested`` emitted.
* Last-node success — workflow transitions to ``done``.
* Node failure under ``FailFastPolicy`` — workflow transitions to ``failed``.
* Stale-cursor idempotency — events for a node the cursor no longer points at are dropped.
* Terminal-status idempotency — events delivered after ``done``/``failed`` are dropped.
"""

from __future__ import annotations

from datetime import UTC, datetime

from shell.application.event_handlers.graph_node_execution_worker import GraphNodeExecutionWorker
from shell.domain.entities.graph_execution import GraphExecution
from shell.domain.entities.graph_node_execution import GraphNodeExecution
from shell.domain.entities.task_execution import TaskExecution
from shell.domain.entities.workflow import Workflow
from shell.domain.events.events import (
    GraphNodeExecutionAdvanced,
    GraphNodeExecutionCompleted,
    GraphNodeExecutionRequested,
    GraphNodeExecutionFailed,
    WorkflowCompleted,
    WorkflowFailed,
)
from shell.domain.value_objects.hash import Hash
from shell.domain.value_objects.ids import (
    GraphDefinitionId,
    GraphExecutionId,
    GraphNodeExecutionId,
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


def _build_graph_execution(uow: InMemoryUnitOfWork, task_execution_name: str, modes: list[str]) -> tuple[TaskExecution, Graph]:
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

    graph_node_executions = [
        GraphNodeExecution(
            id=GraphNodeExecutionId(f"{task_execution.id.value}-n{i}"),
            position=i,
            node_dir=f"/fake/{m}-{i}",
            mode=Mode(m),
            role=m,
            node_type=m,
        )
        for i, m in enumerate(modes)
    ]
    graph_execution = GraphExecution(
        id=GraphExecutionId.generate(),
        task_execution_id=task_execution.id,
        graph_definition_id=GraphDefinitionId("tpl"),
        graph_node_executions=graph_node_executions,
    )
    uow.graph_executions._store[graph_execution.id.value] = graph_execution  # type: ignore[attr-defined]
    return task_execution, graph_execution


async def _persist_running_workflow(
    uow: InMemoryUnitOfWork, task_execution_id: TaskExecutionId, first_node: GraphNodeExecutionId
) -> Workflow:
    wf = Workflow.new(id_=WorkflowId.generate(), task_execution_id=task_execution_id, now=_NOW)
    wf.start_at(
        first_graph_node_execution_id=first_node,
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
) -> GraphNodeExecutionWorker:
    return GraphNodeExecutionWorker(
        uow=uow,
        clock=FakeClock(_NOW),
        id_gen=FakeIdGenerator(),
        runner=runner,
        logger=FakeLogger(),
    )


class TestGraphNodeExecutionWorkerHappyPath:
    async def test_first_node_success_advances_to_second(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(uow, "happy", ["agent", "tool"])
        wf = await _persist_running_workflow(uow, task_execution.id, graph_execution.graph_node_executions[0].id)

        runner = FakeNodeProcessRunner(stdout="ok", returncode=0)
        worker = _make_worker(uow, runner)

        await worker.handle(GraphNodeExecutionRequested.now(wf.id, graph_execution.graph_node_executions[0].id, now=_NOW))

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.running()
        assert stored.cursor.current_graph_node_execution_id == graph_execution.graph_node_executions[1].id

        types = [type(e) for e in uow.committed_events]
        assert GraphNodeExecutionCompleted in types
        assert GraphNodeExecutionAdvanced in types
        assert GraphNodeExecutionRequested in types

    async def test_last_node_success_finishes_workflow(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(uow, "single", ["agent"])
        wf = await _persist_running_workflow(uow, task_execution.id, graph_execution.graph_node_executions[0].id)

        runner = FakeNodeProcessRunner(returncode=0)
        worker = _make_worker(uow, runner)

        await worker.handle(GraphNodeExecutionRequested.now(wf.id, graph_execution.graph_node_executions[0].id, now=_NOW))

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.done()
        assert stored.cursor.current_graph_node_execution_id is None

        types = [type(e) for e in uow.committed_events]
        assert WorkflowCompleted in types


class TestGraphNodeExecutionWorkerFailure:
    async def test_node_failure_aborts_under_fail_fast_policy(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(uow, "fail", ["agent", "tool"])
        wf = await _persist_running_workflow(uow, task_execution.id, graph_execution.graph_node_executions[0].id)

        runner = FakeNodeProcessRunner(returncode=1, stderr="boom")
        worker = _make_worker(uow, runner)

        await worker.handle(GraphNodeExecutionRequested.now(wf.id, graph_execution.graph_node_executions[0].id, now=_NOW))

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.failed()
        assert stored.cursor.current_graph_node_execution_id is None

        types = [type(e) for e in uow.committed_events]
        assert GraphNodeExecutionFailed in types
        assert WorkflowFailed in types
        # Crucially — no advance, no further work requested.
        assert GraphNodeExecutionAdvanced not in types
        assert GraphNodeExecutionRequested not in types


class TestGraphNodeExecutionWorkerIdempotency:
    async def test_stale_cursor_event_is_dropped(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(uow, "stale", ["agent", "tool"])
        wf = await _persist_running_workflow(uow, task_execution.id, graph_execution.graph_node_executions[0].id)

        runner = FakeNodeProcessRunner(returncode=0)
        worker = _make_worker(uow, runner)

        # Worker is asked to process node[1] but the cursor still points at node[0].
        await worker.handle(GraphNodeExecutionRequested.now(wf.id, graph_execution.graph_node_executions[1].id, now=_NOW))

        # Workflow state must be unchanged.
        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.running()
        assert stored.cursor.current_graph_node_execution_id == graph_execution.graph_node_executions[0].id
        # Runner was not called (early return).
        assert runner.calls == []
        # No domain events were published.
        assert uow.committed_events == []

    async def test_terminal_workflow_ignores_event(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(uow, "terminal", ["agent"])
        wf = await _persist_running_workflow(uow, task_execution.id, graph_execution.graph_node_executions[0].id)

        # Force the workflow into ``done`` state directly.
        wf.record_graph_node_execution_result(
            result_id=FakeIdGenerator().new_graph_node_execution_result_id(),
            graph_node_execution_id=graph_execution.graph_node_executions[0].id,
            status=Status.done(),
            now=_NOW,
        )
        wf.finish(_NOW)
        async with uow:
            await uow.workflows.save(wf)
            await uow.commit()

        runner = FakeNodeProcessRunner(returncode=0)
        worker = _make_worker(uow, runner)

        await worker.handle(GraphNodeExecutionRequested.now(wf.id, graph_execution.graph_node_executions[0].id, now=_NOW))

        # Worker should silently ignore the re-delivery.
        assert runner.calls == []
        assert uow.committed_events == []
