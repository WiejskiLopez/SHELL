"""ImportTaskExecutionHandler — imports a task from a markdown file.

This handler is intentionally ignorant of the GraphExcecution aggregate: after a Task
is persisted, the ``TaskExecutionCreated`` event triggers ``BuildGraphExecutionOnTaskExecutionCreated``
which constructs the appropriate Graph from a GraphDefinition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.aggregates.task_execution import TaskExecution
from shell.domain.value_objects.task_execution_body import TaskExecutionBody
from shell.domain.value_objects.task_execution_name import TaskExecutionName

if TYPE_CHECKING:
    from shell.application.commands.commands import ImportTaskExecutionCommand
    from shell.application.ports.ports import (
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
        body = TaskExecutionBody(await self._task_execution_loader.load(cmd.md_path))
        task_execution_name = TaskExecutionName(cmd.task_execution_name)
        current_time = self._clock.now()
        async with self._uow as uow:
            existing = await uow.task_executions.get_current_by_name(task_execution_name)
            if existing:
                existing.supersede()
                await uow.task_executions.save(existing)
            task_execution = TaskExecution.create(
                id_=self._id_gen.new_task_execution_id(),
                name=task_execution_name,
                body=body,
                now=current_time,
            )
            await uow.task_executions.save(task_execution)
            uow.stage_events(task_execution.pull_events())
            await uow.commit()
        return task_execution.id.value
