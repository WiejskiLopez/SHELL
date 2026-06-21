from __future__ import annotations

from shell.application.platform.commands.commands import RunTaskerWorkflowCommand
from shell.domain.execution.events import (
    GraphNodeExecutionFailedEvent,
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
)
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeGraphNodeExecutionProcessRunner,
    FakeIdGenerator,
    InMemoryUnitOfWork,
)
from shell.tests.conftest import _make_task_with_graph_execution, _run_tasker_full


class TestRunTaskerWorkflowPartialFailure:
    async def test_node_failure_stops_execution(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        task_execution, _ = _make_task_with_graph_execution(
            uow, "failing-task", ["agent", "tool"], clock.now()
        )
        cmd = RunTaskerWorkflowCommand(
            task_execution_id=task_execution.id.value, work_dir="/fake/work/dir"
        )
        failing_runner = FakeGraphNodeExecutionProcessRunner(
            stdout="execution failed", returncode=1
        )

        events = await _run_tasker_full(uow, clock, id_gen, cmd, runner=failing_runner)

        assert any(isinstance(e, GraphNodeExecutionFailedEvent) for e in events)
        assert any(isinstance(e, WorkflowFailedEvent) for e in events)
        assert not any(isinstance(e, WorkflowCompletedEvent) for e in events)

        workflows = list(uow.workflows._store.values())  # type: ignore[attr-defined]
        assert len(workflows) == 1
        assert workflows[0].status.value == "failed"
