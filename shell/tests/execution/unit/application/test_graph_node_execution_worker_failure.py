from __future__ import annotations

from shell.domain.execution.events import (
    GraphNodeExecutionFailedEvent,
    GraphNodeExecutionRequestedEvent,
)
from shell.domain.platform.value_objects.status import Status
from shell.infrastructure.platform.persistence.memory import (
    FakeGraphNodeExecutionProcessRunner,
    InMemoryUnitOfWork,
)
from shell.tests.conftest import (
    _NOW,
    _build_graph_execution,
    _make_worker,
    _persist_running_workflow,
)


class TestGraphNodeExecutionWorkerFailure:
    async def test_node_failure_records_failed_and_does_not_abort(self) -> None:
        unit_of_work = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(unit_of_work, "fail", ["agent", "tool"])
        wf = await _persist_running_workflow(
            unit_of_work, task_execution.id, graph_execution.graph_node_executions[0].id
        )

        runner = FakeGraphNodeExecutionProcessRunner(returncode=1, stderr="boom")
        worker = _make_worker(unit_of_work, runner)

        await worker.handle(
            GraphNodeExecutionRequestedEvent.now(
                wf.id, graph_execution.graph_node_executions[0].id, now=_NOW
            )
        )

        stored = await unit_of_work.workflow_repository.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.running()

        types = [type(e) for e in unit_of_work.committed_events]
        assert GraphNodeExecutionFailedEvent in types
