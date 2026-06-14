"""ImportTaskHandler — imports a task from a markdown file.

This handler is intentionally ignorant of the Graph aggregate: after a Task
is persisted, the ``TaskCreated`` event triggers ``BuildGraphOnTaskCreated``
which constructs the appropriate Graph from a TemplateGraph.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.entities.task import Task
from shell_ddd.domain.value_objects.task_body import TaskBody
from shell_ddd.domain.value_objects.task_name import TaskName

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import ImportTaskCommand
    from shell_ddd.application.ports.ports import (
        Clock,
        IdGenerator,
        Logger,
        TaskLoader,
        UnitOfWork,
    )


class ImportTaskHandler:
    def __init__(
            self,
            uow: UnitOfWork,
            clock: Clock,
            id_gen: IdGenerator,
            task_loader: TaskLoader,
            logger: Logger,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._task_loader = task_loader
        self._logger = logger

    async def handle(self, cmd: ImportTaskCommand) -> str:
        body = TaskBody(await self._task_loader.load(cmd.md_path))
        name = TaskName(cmd.task_name)
        current_time = self._clock.now()
        async with self._uow as uow:
            existing = await uow.tasks.get_current_by_name(name)
            if existing:
                existing.supersede()
                await uow.tasks.save(existing)
            task = Task.create(
                id_=self._id_gen.new_task_id(),
                name=name,
                body=body,
                now=current_time,
            )
            await uow.tasks.save(task)
            uow.stage_events(task.pull_events())
            await uow.commit()
        return task.id.value
