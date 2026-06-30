"""TaskExecutionImportHandler — imports a task from a markdown file.

This handler is intentionally ignorant of the GraphExcecution aggregate: after a Task
is persisted, the ``TaskExecutionCreatedEvent`` event triggers ``BuildGraphExecutionOnTaskExecutionCreatedEventHandler``
which constructs the appropriate Graph from a GraphDefinition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
from shell.domain.execution.value_objects.ids import TaskExecutionId
from shell.domain.execution.value_objects.task_execution_body import TaskExecutionBody
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName

if TYPE_CHECKING:
    from shell.application.execution.commands.task_execution_commands import (
        ImportTaskExecutionCommand,
    )
    from shell.application.platform.ports.ports import (
        Clock,
        IdGenerator,
        Logger,
        TaskExecutionLoader,
        UnitOfWork,
    )


class TaskExecutionImportHandler:
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

    async def handle(self, command: ImportTaskExecutionCommand) -> str:
        content = await self._task_execution_loader.load(command.md_path)
        task_execution_name = TaskExecutionName(command.task_execution_name)
        current_time = self._clock.now()
        async with self._unit_of_work as unit_of_work:
            task_execution = TaskExecution.create(
                id_=self._id_generator.new_id(TaskExecutionId),
                name=task_execution_name,
                body=TaskExecutionBody(content),
                now=current_time,
            )
            await unit_of_work.repository(TaskExecutionRepository).save(task_execution)
            unit_of_work.stage_events(task_execution.pull_events())
        return task_execution.id.value
