from __future__ import annotations

import pytest

from shell.application.command_handlers.run_tasker_workflow_handler import RunTaskerWorkflowHandler
from shell.application.commands.commands import RunTaskerWorkflowCommand
from shell.domain.exceptions import TaskExecutionNotFound
from shell.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeIdGenerator,
    InMemoryUnitOfWork,
)


class TestRunTaskerWorkflowEdgeCases:
    async def test_run_workflow_with_nonexistent_task_raises(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        cmd = RunTaskerWorkflowCommand(task_execution_id="ghost-task-id", work_dir="/fake/dir")
        handler = RunTaskerWorkflowHandler(uow=uow, clock=clock, id_gen=id_gen)

        with pytest.raises(TaskExecutionNotFound):
            await handler.handle(cmd)

        assert uow.committed_events == []
