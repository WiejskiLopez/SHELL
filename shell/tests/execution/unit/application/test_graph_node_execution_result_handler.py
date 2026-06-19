"""Unit tests for GraphNodeExecutionResultHandler — Cycle B of the saga.

Each test verifies that, given a workflow with a recorded result,
the handler correctly decides the next step (advance / finish / abort).
"""

from __future__ import annotations

from shell.domain.execution.events import (
    GraphNodeExecutionAdvancedEvent,
    GraphNodeExecutionCompletedEvent,
    GraphNodeExecutionFailedEvent,
    GraphNodeExecutionRequestedEvent,
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
)
from shell.domain.platform.value_objects.status import Status
from shell.infrastructure.platform.persistence.memory import (
    FakeNodeProcessRunner,
    InMemoryUnitOfWork
)

from shell.infrastructure.platform.persistence.memory import FakeIdGenerator

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

        # Arrange: simulate that Cycle A already ran — record result manually
        id_gen = FakeIdGenerator()
        wf.record_graph_node_execution_result(
            result_id=id_gen.new_graph_node_execution_result_id(),
            graph_node_execution_id=graph_execution.graph_node_executions[0].id,
            status=Status.done(),
            now=_NOW,
        )
        async with uow:
            await uow.workflows.save(wf)
            await uow.commit()

        handler = _make_result_handler(uow)

        # Act: Cycle B — result handler decides next step
        result_id = wf.graph_node_execution_results[0].id
        await handler.handle(
            GraphNodeExecutionCompletedEvent.now(
                graph_node_execution_id=graph_execution.graph_node_executions[0].id,
                workflow_id=wf.id,
                graph_node_execution_result_id=result_id,
                now=_NOW,
            )
        )

        # Assert: cursor advanced to the second node
        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.running()
        assert (
            stored.cursor.current_graph_node_execution_id
            == graph_execution.graph_node_executions[1].id
        )

        types = [type(e) for e in uow.committed_events]
        assert GraphNodeExecutionAdvancedEvent in types
        assert GraphNodeExecutionRequestedEvent in types

    async def test_completed_on_last_node_finishes_workflow(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(uow, "fin", ["agent"])
        wf = await _persist_running_workflow(
            uow, task_execution.id, graph_execution.graph_node_executions[0].id
        )

        # Arrange: Cycle A already ran
        id_gen = FakeIdGenerator()
        wf.record_graph_node_execution_result(
            result_id=id_gen.new_graph_node_execution_result_id(),
            graph_node_execution_id=graph_execution.graph_node_executions[0].id,
            status=Status.done(),
            now=_NOW,
        )
        async with uow:
            await uow.workflows.save(wf)
            await uow.commit()

        handler = _make_result_handler(uow)

        result_id = wf.graph_node_execution_results[0].id
        await handler.handle(
            GraphNodeExecutionCompletedEvent.now(
                graph_node_execution_id=graph_execution.graph_node_executions[0].id,
                workflow_id=wf.id,
                graph_node_execution_result_id=result_id,
                now=_NOW,
            )
        )

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.done()
        assert stored.cursor.current_graph_node_execution_id is None

        types = [type(e) for e in uow.committed_events]
        assert WorkflowCompletedEvent in types


class TestGraphNodeExecutionResultHandlerFailure:
    async def test_failed_aborts_under_fail_fast_policy(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(uow, "abort", ["agent", "tool"])
        wf = await _persist_running_workflow(
            uow, task_execution.id, graph_execution.graph_node_executions[0].id
        )

        # Arrange: Cycle A already ran, node failed
        id_gen = FakeIdGenerator()
        wf.record_graph_node_execution_result(
            result_id=id_gen.new_graph_node_execution_result_id(),
            graph_node_execution_id=graph_execution.graph_node_executions[0].id,
            status=Status.failed(),
            now=_NOW,
            stdout="",
            stderr="boom",
        )
        async with uow:
            await uow.workflows.save(wf)
            await uow.commit()

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
        assert stored.cursor.current_graph_node_execution_id is None

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

        # Make workflow terminal
        id_gen = FakeIdGenerator()
        wf.record_graph_node_execution_result(
            result_id=id_gen.new_graph_node_execution_result_id(),
            graph_node_execution_id=graph_execution.graph_node_executions[0].id,
            status=Status.done(),
            now=_NOW,
        )
        wf.finish(_NOW)
        async with uow:
            await uow.workflows.save(wf)
            await uow.commit()

        handler = _make_result_handler(uow)

        # Re-delivery of completed event after finish
        result_id = wf.graph_node_execution_results[0].id
        await handler.handle(
            GraphNodeExecutionCompletedEvent.now(
                graph_node_execution_id=graph_execution.graph_node_executions[0].id,
                workflow_id=wf.id,
                graph_node_execution_result_id=result_id,
                now=_NOW,
            )
        )

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.done()  # unchanged
