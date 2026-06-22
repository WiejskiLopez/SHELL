"""ImportTaskExecutionHandler — imports a task from a markdown file.

This handler is intentionally ignorant of the GraphExcecution aggregate: after a Task
is persisted, the ``TaskExecutionCreatedEvent`` event triggers ``BuildGraphExecutionOnTaskExecutionCreatedEvent``
which constructs the appropriate Graph from a GraphDefinition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
from shell.domain.execution.aggregates.task_execution_state_input.task_execution_state_input import (
    TaskExecutionStateInput,
)
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName

if TYPE_CHECKING:
    from shell.application.platform.commands.commands import ImportTaskExecutionCommand
    from shell.application.platform.ports.ports import (
        Clock,
        IdGenerator,
        Logger,
        TaskExecutionLoader,
        UnitOfWork,
    )


class ImportTaskExecutionHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        task_execution_loader: TaskExecutionLoader,
        logger: Logger,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._task_execution_loader = task_execution_loader
        self._logger = logger

    async def handle(self, cmd: ImportTaskExecutionCommand) -> str:
        content = await self._task_execution_loader.load(cmd.md_path)
        task_execution_name = TaskExecutionName(cmd.task_execution_name)
        current_time = self._clock.now()
        async with self._uow as uow:
            task_execution = TaskExecution.create(
                id_=self._id_gen.new_task_execution_id(),
                name=task_execution_name,
                now=current_time,
            )
            state_input = TaskExecutionStateInput.create(
                id_=self._id_gen.new_task_execution_state_input_id(),
                task_execution_id=task_execution.id,
                payload={"description": content},
                now=current_time,
            )
            await uow.task_executions.save(task_execution)
            await uow.task_execution_state_inputs.save(state_input)
            uow.stage_events(task_execution.pull_events())
        return task_execution.id.value
