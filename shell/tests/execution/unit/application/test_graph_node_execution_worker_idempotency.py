from __future__ import annotations

from shell.domain.execution.events import (
    GraphNodeExecutionRequestedEvent,
)
from shell.infrastructure.platform.persistence.memory import (
    FakeGraphNodeExecutionProcessRunner,
    InMemoryUnitOfWork,
    InMemoryWorkflowRepository,
)
from shell.tests.conftest_helpers import (
    _NOW,
    _build_graph_execution,
    _make_worker,
    _persist_running_workflow,
)


class TestGraphNodeExecutionWorkerIdempotency:
    async def test_terminal_workflow_ignores_event(self) -> None:
        unit_of_work = InMemoryUnitOfWork()
        task_execution, graph_execution, _nodes = _build_graph_execution(unit_of_work, "terminal", ["agent"])
        wf = await _persist_running_workflow(
            unit_of_work, task_execution.id, _nodes[0].id
        )

        wf.finish(now=_NOW)
        async with unit_of_work:
            await unit_of_work.repository(InMemoryWorkflowRepository).save(wf)
            await unit_of_work.commit()

        runner = FakeGraphNodeExecutionProcessRunner(returncode=0)
        worker = _make_worker(unit_of_work, runner)

        await worker.handle(
            GraphNodeExecutionRequestedEvent.now(
                wf.id, _nodes[0].id, now=_NOW
            )
        )

        assert runner.calls == []
        assert unit_of_work.committed_events == []

