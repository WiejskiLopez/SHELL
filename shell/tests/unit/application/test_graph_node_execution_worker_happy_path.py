"""Unit tests for GraphNodeExecutionWorker — happy path (Cycle A only).

The worker only records the result and emits completion/failure.
Next-step decisions are verified in the GraphNodeExecutionResultHandler tests.
"""

from __future__ import annotations

from shell.domain.events.events import (
    GraphNodeExecutionCompleted,
    GraphNodeExecutionFailed,
    GraphNodeExecutionRequested,
)
from shell.domain.value_objects.status import Status
from shell.infrastructure.persistence.memory import (
    FakeNodeProcessRunner,
    InMemoryUnitOfWork,
)

from .conftest import _NOW, _build_graph_execution, _make_worker, _persist_running_workflow


class TestGraphNodeExecutionWorkerHappyPath:
    async def test_first_node_success_records_result_and_does_not_advance(self) -> None:
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
        # Cursor MUST NOT advance — that's Cycle B's job
        assert stored.status == Status.running()
        assert (
            stored.cursor.current_graph_node_execution_id
            == graph_execution.graph_node_executions[0].id
        )

        types = [type(e) for e in uow.committed_events]
        assert GraphNodeExecutionCompleted in types
        # These are emitted by Cycle B (GraphNodeExecutionResultHandler):
        assert GraphNodeExecutionFailed not in types

    async def test_last_node_success_records_result_and_does_not_finish(self) -> None:
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
        # Worker must NOT finish the workflow — only record the result
        assert stored.status == Status.running()
        assert stored.cursor.current_graph_node_execution_id is not None

        types = [type(e) for e in uow.committed_events]
        assert GraphNodeExecutionCompleted in types
