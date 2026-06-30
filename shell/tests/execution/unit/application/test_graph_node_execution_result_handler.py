from __future__ import annotations

from shell.domain.execution.events import (
    GraphNodeExecutionAdvancedEvent,
    GraphNodeExecutionCompletedEvent,
    GraphNodeExecutionFailedEvent,
    GraphNodeExecutionRequestedEvent,
    WorkflowAbortedEvent,
    WorkflowCompletedEvent,
)
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.infrastructure.platform.persistence.memory import (
    InMemoryUnitOfWork,
    InMemoryWorkflowRepository,
)
from shell.tests.conftest_helpers import (
    _NOW,
    _build_graph_execution,
    _make_result_handler,
    _persist_running_workflow,
)


class TestGraphNodeExecutionResultHandlerHappyPath:
    async def test_completed_advances_to_next_node(self) -> None:
        unit_of_work = InMemoryUnitOfWork()
        task_execution, graph_execution, _nodes = _build_graph_execution(
            unit_of_work, "adv", ["agent", "tool"]
        )
        wf = await _persist_running_workflow(unit_of_work, task_execution.id, _nodes[0].id)

        handler = _make_result_handler(unit_of_work)

        await handler.handle(
            GraphNodeExecutionCompletedEvent.now(
                node_id=_nodes[0].id,
                workflow_id=wf.id,
                now=CreatedAt.from_datetime(_NOW),
            )
        )

        stored = await unit_of_work.repository(InMemoryWorkflowRepository).get_by_id(wf.id)
        assert stored is not None
        assert stored.status == WorkflowStatus.ACTIVE

        types = [type(e) for e in unit_of_work.committed_events]
        assert GraphNodeExecutionAdvancedEvent in types
        assert GraphNodeExecutionRequestedEvent in types

    async def test_completed_on_last_node_finishes_workflow(self) -> None:
        unit_of_work = InMemoryUnitOfWork()
        task_execution, graph_execution, _nodes = _build_graph_execution(
            unit_of_work, "fin", ["agent"]
        )
        wf = await _persist_running_workflow(unit_of_work, task_execution.id, _nodes[0].id)

        handler = _make_result_handler(unit_of_work)

        await handler.handle(
            GraphNodeExecutionCompletedEvent.now(
                node_id=_nodes[0].id,
                workflow_id=wf.id,
                now=CreatedAt.from_datetime(_NOW),
            )
        )

        stored = await unit_of_work.repository(InMemoryWorkflowRepository).get_by_id(wf.id)
        assert stored is not None
        assert stored.status == WorkflowStatus.COMPLETED

        types = [type(e) for e in unit_of_work.committed_events]
        assert WorkflowCompletedEvent in types


class TestGraphNodeExecutionResultHandlerFailure:
    async def test_failed_aborts_under_fail_fast_policy(self) -> None:
        unit_of_work = InMemoryUnitOfWork()
        task_execution, graph_execution, _nodes = _build_graph_execution(
            unit_of_work, "abort", ["agent", "tool"]
        )
        wf = await _persist_running_workflow(unit_of_work, task_execution.id, _nodes[0].id)

        handler = _make_result_handler(unit_of_work)

        await handler.handle(
            GraphNodeExecutionFailedEvent.now(
                node_id=_nodes[0].id,
                workflow_id=wf.id,
                reason="boom",
                now=CreatedAt.from_datetime(_NOW),
            )
        )

        stored = await unit_of_work.repository(InMemoryWorkflowRepository).get_by_id(wf.id)
        assert stored is not None
        assert stored.status == WorkflowStatus.ABORTED

        types = [type(e) for e in unit_of_work.committed_events]
        assert WorkflowAbortedEvent in types
        assert GraphNodeExecutionAdvancedEvent not in types
        assert GraphNodeExecutionRequestedEvent not in types


class TestGraphNodeExecutionResultHandlerIdempotency:
    async def test_terminal_workflow_ignores_result_event(self) -> None:
        unit_of_work = InMemoryUnitOfWork()
        task_execution, graph_execution, _nodes = _build_graph_execution(
            unit_of_work, "term", ["agent"]
        )
        wf = await _persist_running_workflow(unit_of_work, task_execution.id, _nodes[0].id)

        wf.finish(now=_NOW)
        async with unit_of_work:
            await unit_of_work.repository(InMemoryWorkflowRepository).save(wf)
            await unit_of_work.commit()

        handler = _make_result_handler(unit_of_work)

        await handler.handle(
            GraphNodeExecutionCompletedEvent.now(
                node_id=_nodes[0].id,
                workflow_id=wf.id,
                now=CreatedAt.from_datetime(_NOW),
            )
        )

        stored = await unit_of_work.repository(InMemoryWorkflowRepository).get_by_id(wf.id)
        assert stored is not None
        assert stored.status == WorkflowStatus.COMPLETED
