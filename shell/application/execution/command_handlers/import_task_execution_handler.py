"""ImportTaskExecutionHandler — imports a task from a markdown file.

This handler is intentionally ignorant of the GraphExcecution aggregate: after a Task
is persisted, the ``TaskExecutionCreatedEvent`` event triggers ``BuildGraphExecutionOnTaskExecutionCreatedEventHandler``
which constructs the appropriate Graph from a GraphDefinition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
    TaskExecutionState,
)
from shell.domain.execution.value_objects.state_data import StateData
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.platform.value_objects.created_at import CreatedAt

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
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
        task_execution_loader: TaskExecutionLoader,
        logger: Logger,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator
        self._task_execution_loader = task_execution_loader
        self._logger = logger

    async def handle(self, import_task_execution_command: ImportTaskExecutionCommand) -> str:
        content = await self._task_execution_loader.load(import_task_execution_command.md_path)
        task_execution_name = TaskExecutionName(import_task_execution_command.task_execution_name)
        current_time = self._clock.now()
        async with self._unit_of_work as unit_of_work:
            task_execution = TaskExecution.create(
                id_=self._id_generator.new_task_execution_id(),
                name=task_execution_name,
                now=current_time,
            )
            state_input = TaskExecutionState.create(
                id_=self._id_generator.new_task_execution_state_id(),
                task_execution_id=task_execution.id,
                payload=StateData({"description": content}),
                now=CreatedAt.from_datetime(current_time),
            )
            await unit_of_work.task_execution_repository.save(task_execution)
            await unit_of_work.task_execution_state_repository.save(state_input)
            unit_of_work.stage_events(task_execution.pull_events())
        return task_execution.id.value
