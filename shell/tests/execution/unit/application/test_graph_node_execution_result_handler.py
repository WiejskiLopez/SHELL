from __future__ import annotations

from shell.domain.execution.aggregates.workflow.events.graph_node_execution_advanced_event import (
    GraphNodeExecutionAdvancedEvent,
)
from shell.domain.execution.aggregates.workflow.events.graph_node_execution_requested_event import (
    GraphNodeExecutionRequestedEvent,
)
from shell.domain.execution.events import (
    GraphNodeExecutionCompletedEvent,
    GraphNodeExecutionFailedEvent,
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
)
from shell.domain.platform.value_objects.status import Status
from shell.infrastructure.platform.persistence.memory import (
    InMemoryUnitOfWork,
)
from shell.tests.conftest import (
    _NOW,
    _build_graph_execution,
    _make_result_handler,
    _persist_running_workflow,
)


class TestGraphNodeExecutionResultHandlerHappyPath:
    async def test_completed_advances_to_next_node(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(uow, "adv", ["agent", "tool"])
        wf = await _persist_running_workflow(
            uow, task_execution.id, graph_execution.graph_node_executions[0].id
        )

        handler = _make_result_handler(uow)

        await handler.handle(
            GraphNodeExecutionCompletedEvent.now(
                graph_node_execution_id=graph_execution.graph_node_executions[0].id,
                workflow_id=wf.id,
                result_id=None,
                now=_NOW,
            )
        )

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.running()

        types = [type(e) for e in uow.committed_events]
        assert GraphNodeExecutionAdvancedEvent in types
        assert GraphNodeExecutionRequestedEvent in types

    async def test_completed_on_last_node_finishes_workflow(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(uow, "fin", ["agent"])
        wf = await _persist_running_workflow(
            uow, task_execution.id, graph_execution.graph_node_executions[0].id
        )

        handler = _make_result_handler(uow)

        await handler.handle(
            GraphNodeExecutionCompletedEvent.now(
                graph_node_execution_id=graph_execution.graph_node_executions[0].id,
                workflow_id=wf.id,
                result_id=None,
                now=_NOW,
            )
        )

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.done()

        types = [type(e) for e in uow.committed_events]
        assert WorkflowCompletedEvent in types


class TestGraphNodeExecutionResultHandlerFailure:
    async def test_failed_aborts_under_fail_fast_policy(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(uow, "abort", ["agent", "tool"])
        wf = await _persist_running_workflow(
            uow, task_execution.id, graph_execution.graph_node_executions[0].id
        )

        handler = _make_result_handler(uow)

        await handler.handle(
            GraphNodeExecutionFailedEvent.now(
                graph_node_execution_id=graph_execution.graph_node_executions[0].id,
                workflow_id=wf.id,
                reason="boom",
                now=_NOW,
            )
        )

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.failed()

        types = [type(e) for e in uow.committed_events]
        assert WorkflowFailedEvent in types
        assert GraphNodeExecutionAdvancedEvent not in types
        assert GraphNodeExecutionRequestedEvent not in types


class TestGraphNodeExecutionResultHandlerIdempotency:
    async def test_terminal_workflow_ignores_result_event(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(uow, "term", ["agent"])
        wf = await _persist_running_workflow(
            uow, task_execution.id, graph_execution.graph_node_executions[0].id
        )

        wf.finish(now=_NOW)
        async with uow:
            await uow.workflows.save(wf)
            await uow.commit()

        handler = _make_result_handler(uow)

        await handler.handle(
            GraphNodeExecutionCompletedEvent.now(
                graph_node_execution_id=graph_execution.graph_node_executions[0].id,
                workflow_id=wf.id,
                result_id=None,
                now=_NOW,
            )
        )

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.done()
