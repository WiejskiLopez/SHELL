"""Unit tests for GraphNodeExecutionWorker — failure path (Cycle A only).

The worker only records the result and emits the failure event.
Next-step decisions (abort/continue) are verified in the
GraphNodeExecutionResultHandler tests.
"""

from __future__ import annotations

from shell.domain.events.events import (
    GraphNodeExecutionFailed,
    GraphNodeExecutionRequested,
)
from shell.domain.value_objects.status import Status
from shell.infrastructure.persistence.memory import (
    FakeNodeProcessRunner,
    InMemoryUnitOfWork,
)

from .conftest import _NOW, _build_graph_execution, _make_worker, _persist_running_workflow


class TestGraphNodeExecutionWorkerFailure:
    async def test_node_failure_records_failed_and_does_not_abort(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(uow, "fail", ["agent", "tool"])
        wf = await _persist_running_workflow(
            uow, task_execution.id, graph_execution.graph_node_executions[0].id
        )

        runner = FakeNodeProcessRunner(returncode=1, stderr="boom")
        worker = _make_worker(uow, runner)

        await worker.handle(
            GraphNodeExecutionRequested.now(
                wf.id, graph_execution.graph_node_executions[0].id, now=_NOW
            )
        )

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        # Worker must NOT abort — only record the failed result
        assert stored.status == Status.running()
        assert (
            stored.cursor.current_graph_node_execution_id
            == graph_execution.graph_node_executions[0].id
        )

        types = [type(e) for e in uow.committed_events]
        assert GraphNodeExecutionFailed in types
