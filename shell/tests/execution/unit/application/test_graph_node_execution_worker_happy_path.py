from __future__ import annotations

from shell.domain.execution.events import (
    GraphNodeExecutionCompletedEvent,
    GraphNodeExecutionFailedEvent,
    GraphNodeExecutionRequestedEvent,
)
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus
from shell.infrastructure.platform.persistence.memory import (
    FakeGraphNodeExecutionProcessRunner,
    InMemoryUnitOfWork,
    InMemoryWorkflowRepository,
)
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.tests.conftest_helpers import (
    _NOW,
    _build_graph_execution,
    _make_worker,
    _persist_running_workflow,
)


class TestGraphNodeExecutionWorkerHappyPath:
    async def test_first_node_success_records_result_and_does_not_advance(self) -> None:
        unit_of_work = InMemoryUnitOfWork()
        task_execution, graph_execution, _nodes = _build_graph_execution(unit_of_work, "happy", ["agent", "tool"])
        wf = await _persist_running_workflow(
            unit_of_work, task_execution.id, _nodes[0].id
        )

        runner = FakeGraphNodeExecutionProcessRunner(stdout="ok", returncode=0)
        worker = _make_worker(unit_of_work, runner)

        await worker.handle(
            GraphNodeExecutionRequestedEvent.now(
                wf.id, _nodes[0].id, now=CreatedAt.from_datetime(_NOW)
            )
        )

        stored = await unit_of_work.repository(InMemoryWorkflowRepository).get_by_id(wf.id)
        assert stored is not None
        assert stored.status == WorkflowStatus.ACTIVE

        types = [type(e) for e in unit_of_work.committed_events]
        assert GraphNodeExecutionCompletedEvent in types
        assert GraphNodeExecutionFailedEvent not in types

    async def test_last_node_success_records_result_and_does_not_finish(self) -> None:
        unit_of_work = InMemoryUnitOfWork()
        task_execution, graph_execution, _nodes = _build_graph_execution(unit_of_work, "single", ["agent"])
        wf = await _persist_running_workflow(
            unit_of_work, task_execution.id, _nodes[0].id
        )

        runner = FakeGraphNodeExecutionProcessRunner(returncode=0)
        worker = _make_worker(unit_of_work, runner)

        await worker.handle(
            GraphNodeExecutionRequestedEvent.now(
                wf.id, _nodes[0].id, now=CreatedAt.from_datetime(_NOW)
            )
        )

        stored = await unit_of_work.repository(InMemoryWorkflowRepository).get_by_id(wf.id)
        assert stored is not None
        assert stored.status == WorkflowStatus.ACTIVE

        types = [type(e) for e in unit_of_work.committed_events]
        assert GraphNodeExecutionCompletedEvent in types
