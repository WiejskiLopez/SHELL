from __future__ import annotations

from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_completed_event import (
    GraphNodeExecutionCompletedEvent,
)
from shell.domain.execution.events import GraphNodeExecutionRequestedEvent
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


class TestGraphNodeExecutionWorkerIdempotency:
    async def test_terminal_workflow_ignores_event(self) -> None:
        unit_of_work = InMemoryUnitOfWork()
        task_execution, graph_execution = _build_graph_execution(unit_of_work, "terminal", ["agent"])
        wf = await _persist_running_workflow(
            unit_of_work, task_execution.id, graph_execution.graph_node_executions[0].id
        )

        wf.finish(now=_NOW)
        async with unit_of_work:
            await unit_of_work.workflow_repository.save(wf)
            await unit_of_work.commit()

        runner = FakeGraphNodeExecutionProcessRunner(returncode=0)
        worker = _make_worker(unit_of_work, runner)

        await worker.handle(
            GraphNodeExecutionRequestedEvent.now(
                wf.id, graph_execution.graph_node_executions[0].id, now=_NOW
            )
        )

        assert runner.calls == []
        assert unit_of_work.committed_events == []
