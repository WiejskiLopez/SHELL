from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.execution.command_handlers.workflow_run_tasker_handler import (
    WorkflowRunTaskerHandler,
)
from shell.application.execution.commands.workflow_commands import RunTaskerWorkflowCommand
from shell.domain.execution.aggregates.workflow.events.workflow_started_event import (
    WorkflowStartedEvent,
)

if TYPE_CHECKING:
    from shell.infrastructure.platform.persistence.memory import (
        FakeClock,
        FakeIdGenerator,
        InMemoryUnitOfWork,
    )


class TestRunTaskerWorkflowEdgeCases:
    async def test_run_workflow_with_nonexistent_task_raises(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        command = RunTaskerWorkflowCommand(task_execution_id="ghost-task-id", work_dir="/fake/dir")
        handler = WorkflowRunTaskerHandler(
            unit_of_work=unit_of_work, clock=clock, id_generator=id_generator
        )

        wf_id = await handler.handle(command)

        assert wf_id is not None
        assert any(
            isinstance(e, WorkflowStartedEvent) for e in unit_of_work.committed_events
        )
