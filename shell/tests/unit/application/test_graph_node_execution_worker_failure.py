"""Unit tests for GraphNodeExecutionWorker — failure path."""

from __future__ import annotations

from shell.domain.events.events import (
    GraphNodeExecutionAdvanced,
    GraphNodeExecutionFailed,
    GraphNodeExecutionRequested,
    WorkflowFailed,
)
from shell.domain.value_objects.status import Status
from shell.infrastructure.persistence.memory.memory import (
    FakeNodeProcessRunner,
    InMemoryUnitOfWork,
)

from .conftest import _NOW, _build_graph_execution, _make_worker, _persist_running_workflow


class TestGraphNodeExecutionWorkerFailure:
    async def test_node_failure_aborts_under_fail_fast_policy(self) -> None:
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
        assert stored.status == Status.failed()
        assert stored.cursor.current_graph_node_execution_id is None

        types = [type(e) for e in uow.committed_events]
        assert GraphNodeExecutionFailed in types
        assert WorkflowFailed in types
        assert GraphNodeExecutionAdvanced not in types
        assert GraphNodeExecutionRequested not in types
