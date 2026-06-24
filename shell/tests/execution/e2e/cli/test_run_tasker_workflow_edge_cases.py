from __future__ import annotations

import pytest
from shell.application.execution.command_handlers.run_tasker_workflow_handler import (
    RunTaskerWorkflowHandler,
)
from shell.application.platform.commands.commands import RunTaskerWorkflowCommand
from shell.domain.execution.exceptions import TaskExecutionNotFound
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,  # noqa: TC002 — FakeClock używany w sygnaturach fixture'ów pytest
    FakeIdGenerator,  # noqa: TC002 — FakeIdGenerator używany w sygnaturach fixture'ów pytest
    InMemoryUnitOfWork,  # noqa: TC002 — InMemoryUnitOfWork używany w sygnaturach fixture'ów pytest
)


class TestRunTaskerWorkflowEdgeCases:
    async def test_run_workflow_with_nonexistent_task_raises(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        command = RunTaskerWorkflowCommand(task_execution_id="ghost-task-id", work_dir="/fake/dir")
        handler = RunTaskerWorkflowHandler(uow=unit_of_work, clock=clock, id_generator=id_generator)

        with pytest.raises(TaskExecutionNotFound):
            await handler.handle(command)

        assert unit_of_work.committed_events == []
