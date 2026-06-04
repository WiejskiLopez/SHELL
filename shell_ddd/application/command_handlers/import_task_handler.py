"""ImportTaskHandler — imports a task from markdown + yaml files."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.entities.task import Task
from shell_ddd.domain.events.events import TaskImported
from shell_ddd.domain.value_objects.task_name import TaskName

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import ImportTaskCommand
    from shell_ddd.application.ports.ports import (
        Clock,
        EventPublisher,
        IdGenerator,
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
        events: EventPublisher,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._task_loader = task_loader
        self._events = events

    async def handle(self, cmd: ImportTaskCommand) -> str:
        body_md, body_yaml_raw = await self._task_loader.load(cmd.md_path, cmd.yaml_path)
        name = TaskName(cmd.task_name)
        task = Task.new(
            id_=self._id_gen.new_task_id(),
            name=name,
            body_md=body_md,
            body_yaml_raw=body_yaml_raw,
            now=self._clock.now(),
        )
        async with self._uow as uow:
            # mark previous versions non-current
            existing = await uow.tasks.get_current_by_name(name)
            if existing:
                existing.is_current = False
                await uow.tasks.save(existing)
            await uow.tasks.save(task)
            await uow.commit()
        await self._events.publish([TaskImported.now(task.id, name)])
        return task.id.value
