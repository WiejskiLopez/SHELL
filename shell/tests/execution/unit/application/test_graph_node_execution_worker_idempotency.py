"""Unit tests for GraphNodeExecutionWorker — idempotency."""

from __future__ import annotations

from shell.domain.execution.events import GraphNodeExecutionRequestedEvent
from shell.domain.platform.value_objects.status import Status
from shell.infrastructure.platform.persistence.memory import (
    FakeGraphNodeExecutionProcessRunner,
    FakeIdGenerator,
    InMemoryUnitOfWork,
)
from shell.tests.conftest import (
    _NOW,
    _build_graph_execution,
    _make_worker,
    _persist_running_workflow,
)


class TestGraphNodeExecutionWorkerIdempotency:
    async def test_stale_cursor_event_is_dropped(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(uow, "stale", ["agent", "tool"])
        wf = await _persist_running_workflow(
            uow, task_execution.id, graph_execution.graph_node_executions[0].id
        )

        runner = FakeGraphNodeExecutionProcessRunner(returncode=0)
        worker = _make_worker(uow, runner)

        await worker.handle(
            GraphNodeExecutionRequestedEvent.now(
                wf.id, graph_execution.graph_node_executions[1].id, now=_NOW
            )
        )

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.running()
        assert (
            stored.cursor.current_graph_node_execution_id
            == graph_execution.graph_node_executions[0].id
        )
        assert runner.calls == []
        assert uow.committed_events == []

    async def test_terminal_workflow_ignores_event(self) -> None:
        uow = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(uow, "terminal", ["agent"])
        wf = await _persist_running_workflow(
            uow, task_execution.id, graph_execution.graph_node_executions[0].id
        )

        wf.record_graph_node_execution_result(
            result_id=FakeIdGenerator().new_graph_node_execution_result_id(),
            graph_node_execution_id=graph_execution.graph_node_executions[0].id,
            status=Status.done(),
            now=_NOW,
        )
        wf.finish(_NOW)
        async with uow:
            await uow.workflows.save(wf)
            await uow.commit()

        runner = FakeGraphNodeExecutionProcessRunner(returncode=0)
        worker = _make_worker(uow, runner)

        await worker.handle(
            GraphNodeExecutionRequestedEvent.now(
                wf.id, graph_execution.graph_node_executions[0].id, now=_NOW
            )
        )

        assert runner.calls == []
        assert uow.committed_events == []
