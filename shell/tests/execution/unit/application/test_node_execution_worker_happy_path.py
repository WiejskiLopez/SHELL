from __future__ import annotations

from shell.domain.execution.aggregates.node_execution.events.node_execution_completed_event import (
    NodeExecutionCompletedEvent,
)
from shell.domain.execution.aggregates.node_execution.events.node_execution_failed_event import (
    NodeExecutionFailedEvent,
)
from shell.domain.execution.aggregates.workflow.events.node_execution_requested_event import (
    NodeExecutionRequestedEvent,
)
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.infrastructure.platform.persistence.memory import (
    FakeNodeExecutionProcessRunner,
    InMemoryUnitOfWork,
    InMemoryWorkflowRepository,
)
from shell.tests.conftest_helpers import (
    _NOW,
    _build_graph_execution,
    _make_worker,
    _persist_running_workflow,
)


class TestNodeExecutionWorkerHappyPath:
    async def test_first_node_success_records_result_and_does_not_advance(self) -> None:
        unit_of_work = InMemoryUnitOfWork()
        task_execution, graph_execution, _nodes = _build_graph_execution(
            unit_of_work, "happy", ["agent", "tool"]
        )
        wf = await _persist_running_workflow(unit_of_work, task_execution.id, _nodes[0].id)

        runner = FakeNodeExecutionProcessRunner(stdout="ok", returncode=0)
        worker = _make_worker(unit_of_work, runner)

        await worker.handle(
            NodeExecutionRequestedEvent.now(
                wf.id, _nodes[0].id, now=CreatedAt.from_datetime(_NOW)
            )
        )

        stored = await unit_of_work.repository(InMemoryWorkflowRepository).get_by_id(wf.id)
        assert stored is not None
        assert stored.status == WorkflowStatus.ACTIVE

        types = [type(e) for e in unit_of_work.committed_events]
        assert NodeExecutionCompletedEvent in types
        assert NodeExecutionFailedEvent not in types

    async def test_last_node_success_records_result_and_does_not_finish(self) -> None:
        unit_of_work = InMemoryUnitOfWork()
        task_execution, graph_execution, _nodes = _build_graph_execution(
            unit_of_work, "single", ["agent"]
        )
        wf = await _persist_running_workflow(unit_of_work, task_execution.id, _nodes[0].id)

        runner = FakeNodeExecutionProcessRunner(returncode=0)
        worker = _make_worker(unit_of_work, runner)

        await worker.handle(
            NodeExecutionRequestedEvent.now(
                wf.id, _nodes[0].id, now=CreatedAt.from_datetime(_NOW)
            )
        )

        stored = await unit_of_work.repository(InMemoryWorkflowRepository).get_by_id(wf.id)
        assert stored is not None
        assert stored.status == WorkflowStatus.ACTIVE

        types = [type(e) for e in unit_of_work.committed_events]
        assert NodeExecutionCompletedEvent in types
