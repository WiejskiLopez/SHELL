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
            event_publisher: EventPublisher,
            logger: Logger,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._task_loader = task_loader
        self._event_publisher = event_publisher
        self._logger = logger

    async def handle(self, cmd: ImportTaskCommand) -> str:
        body_md = await self._task_loader.load(cmd.md_path)
        name = TaskName(cmd.task_name)
        current_time = self._clock.now()
        async with self._uow as uow:
            template_graph = await uow.template_graphs.get_template_graph_by_name("base_planner")
            self._logger.info(
                "TemplateGraph loaded",
                exists=template_graph is not None,
                id=getattr(template_graph, "id", None),
            )
            if not template_graph:
                self._logger.error("TemplateGraph base_planner NOT FOUND")
                raise TemplateGraphNotFoundException("Template Graph not found")
            # mark previous versions non-current
            existing = await uow.tasks.get_current_by_name(name)
            self._logger.info(
                "Existing task lookup",
                task_id=existing.id.value if existing else None,
            )
            if existing:
                existing.is_current = False
                await uow.tasks.save(existing)
                self._logger.info(
                    "Marked previous task as non-current",
                    task_id=existing.id.value,
                )

            task = Task.new(
                id_=self._id_gen.new_task_id(),
                name=name,
                body_md=body_md,
                template_graph_id=template_graph.id,
                now=current_time,
            )
            self._logger.info(
                "New task created",
                task_id=task.id.value,
                template_graph_id=task.template_graph_id.value,
            )
            await uow.tasks.save(task)
            uow.stage_events([TaskImported.now(task.id, name, now=current_time)])
            await uow.commit()
        await self._event_publisher.publish(uow.events)
        self._logger.info("Event published", task_id=task.id.value)
        return task.id.value
