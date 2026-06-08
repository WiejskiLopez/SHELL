"""ImportTaskHandler — imports a task from markdown + yaml files."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.application.exceptions import TemplateGraphNotFoundException
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

import logging

logger = logging.getLogger(__name__)


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
        body_md, _ = await self._task_loader.load(cmd.md_path, "")
        name = TaskName(cmd.task_name)
        async with self._uow as uow:
            template_graph = await uow.template_graphs.get_template_graph_by_name("base_planner")
            logger.info(
                "TemplateGraph loaded: exists=%s id=%s",
                template_graph is not None,
                getattr(template_graph, "id", None),
                )
            if not template_graph:
                logger.error("TemplateGraph base_planner NOT FOUND")
                raise TemplateGraphNotFoundException("Template Graph not found")
            # mark previous versions non-current
            existing = await uow.tasks.get_current_by_name(name)
            logger.info("Existing task: %s", existing.id.value if existing else None)
            if existing:
                existing.is_current = False
                await uow.tasks.save(existing)
                logger.info("Marked previous task as non-current: %s", existing.id.value)

            task = Task.new(
                id_=self._id_gen.new_task_id(),
                name=name,
                body_md=body_md,
                template_graph_id=template_graph.id,
                now=self._clock.now(),
            )
            logger.info(
                "New task created: id=%s template_graph_id=%s",
                task.id.value,
                task.template_graph_id.value,
            )
            await uow.tasks.save(task)
            await uow.commit()
        await self._events.publish([TaskImported.now(task.id, name)])
        logger.info("Event published: task_id=%s", task.id.value)
        return task.id.value
