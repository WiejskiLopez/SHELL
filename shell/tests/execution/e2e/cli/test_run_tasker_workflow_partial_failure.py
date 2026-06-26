from __future__ import annotations

from shell.application.platform.commands.commands import RunTaskerWorkflowCommand
from shell.domain.execution.events import (
    GraphNodeExecutionFailedEvent,
    WorkflowCompletedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_aborted_event import (
    WorkflowAbortedEvent,
)
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeGraphNodeExecutionProcessRunner,
    FakeIdGenerator,
    InMemoryUnitOfWork,
)
from shell.tests.conftest_helpers import _make_task_with_graph_execution, _run_tasker_full


class TestRunTaskerWorkflowPartialFailure:
    async def test_node_failure_stops_execution(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        task_execution, _ = _make_task_with_graph_execution(
            unit_of_work, "failing-task", ["agent", "tool"], clock.now()
        )
        command = RunTaskerWorkflowCommand(
            task_execution_id=task_execution.id.value, work_dir="/fake/work/dir"
        )
        failing_runner = FakeGraphNodeExecutionProcessRunner(
            stdout="execution failed", returncode=1
        )

        events = await _run_tasker_full(unit_of_work, clock, id_generator, command, runner=failing_runner)

        assert any(isinstance(e, GraphNodeExecutionFailedEvent) for e in events)
        assert any(isinstance(e, WorkflowAbortedEvent) for e in events)
        assert not any(isinstance(e, WorkflowCompletedEvent) for e in events)

        workflows = list(unit_of_work.workflow_repository._store.values())
        assert len(workflows) == 1
        assert workflows[0].status.value == "aborted"
