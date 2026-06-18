from __future__ import annotations

from shell.application.commands.commands import RunTaskerWorkflowCommand
from shell.domain.events.events import (
    GraphNodeExecutionFailed,
    WorkflowCompleted,
    WorkflowFailed,
)
from shell.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeIdGenerator,
    FakeNodeProcessRunner,
    InMemoryUnitOfWork,
)

from .conftest import _make_task_with_graph_execution, _run_tasker_full


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
        failing_runner = FakeNodeProcessRunner(stdout="execution failed", returncode=1)

        events = await _run_tasker_full(uow, clock, id_gen, cmd, runner=failing_runner)

        assert any(isinstance(e, GraphNodeExecutionFailed) for e in events)
        assert any(isinstance(e, WorkflowFailed) for e in events)
        assert not any(isinstance(e, WorkflowCompleted) for e in events)

        workflows = list(uow.workflows._store.values())  # type: ignore[attr-defined]
        assert len(workflows) == 1
        assert workflows[0].status.value == "failed"
