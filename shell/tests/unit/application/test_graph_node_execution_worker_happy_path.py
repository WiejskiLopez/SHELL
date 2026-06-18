"""Unit tests for GraphNodeExecutionWorker — happy path."""

from __future__ import annotations

from shell.domain.events.events import (
    GraphNodeExecutionAdvanced,
    GraphNodeExecutionCompleted,
    GraphNodeExecutionRequested,
    WorkflowCompleted,
)
from shell.domain.value_objects.status import Status
from shell.infrastructure.persistence.memory.memory import (
    FakeNodeProcessRunner,
    InMemoryUnitOfWork,
)

from .conftest import _NOW, _build_graph_execution, _make_worker, _persist_running_workflow


class TestGraphNodeExecutionWorkerHappyPath:
    async def test_first_node_success_advances_to_second(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(uow, "happy", ["agent", "tool"])
        wf = await _persist_running_workflow(
            uow, task_execution.id, graph_execution.graph_node_executions[0].id
        )

        runner = FakeNodeProcessRunner(stdout="ok", returncode=0)
        worker = _make_worker(uow, runner)

        await worker.handle(
            GraphNodeExecutionRequested.now(
                wf.id, graph_execution.graph_node_executions[0].id, now=_NOW
            )
        )

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.running()
        assert (
            stored.cursor.current_graph_node_execution_id
            == graph_execution.graph_node_executions[1].id
        )

        types = [type(e) for e in uow.committed_events]
        assert GraphNodeExecutionCompleted in types
        assert GraphNodeExecutionAdvanced in types
        assert GraphNodeExecutionRequested in types

    async def test_last_node_success_finishes_workflow(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(uow, "single", ["agent"])
        wf = await _persist_running_workflow(
            uow, task_execution.id, graph_execution.graph_node_executions[0].id
        )

        runner = FakeNodeProcessRunner(returncode=0)
        worker = _make_worker(uow, runner)

        await worker.handle(
            GraphNodeExecutionRequested.now(
                wf.id, graph_execution.graph_node_executions[0].id, now=_NOW
            )
        )

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.done()
        assert stored.cursor.current_graph_node_execution_id is None

        types = [type(e) for e in uow.committed_events]
        assert WorkflowCompleted in types
