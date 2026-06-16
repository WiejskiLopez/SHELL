"""BuildGraphOnTaskCreated — reacts to TaskCreated and builds a Graph.

The Task aggregate is intentionally agnostic of which Graph realises it.
This handler bridges that gap: when a Task is created, it materialises a
Graph from a TemplateGraph (default name: ``base_planner``), persists it
in its own transactional boundary, and forwards the resulting domain
events (``GraphBuilt``) downstream.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.exceptions import TemplateGraphNotFoundException
from shell.domain.entities.graph import Graph

if TYPE_CHECKING:
    from shell.application.ports.ports import (
        Clock,
        IdGenerator,
        Logger,
        UnitOfWork,
    )
    from shell.domain.events.events import TaskCreated


DEFAULT_TEMPLATE_NAME = "base_planner"


class BuildGraphOnTaskCreated:
    """Event handler — listens to ``TaskCreated`` and builds a Graph."""

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        logger: Logger,
        template_name: str = DEFAULT_TEMPLATE_NAME,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._logger = logger
        self._template_name = template_name

    async def handle(self, event: TaskCreated) -> None:
        self._logger.info(
            "Handle TaskCreated:",
            task_id=event.task_id.value,
        )
        now = self._clock.now()
        async with self._uow as uow:
            existing = await uow.graphs.get_by_task_id(event.task_id)
            if existing is not None:
                self._logger.info(
                    "Graph already exists for task — skipping build",
                    task_id=event.task_id.value,
                )
                return

            template = await uow.template_graphs.get_template_graph_by_name(
                self._template_name,
            )
            if template is None:
                raise TemplateGraphNotFoundException(
                    f"Template graph {self._template_name!r} not found",
                )

            graph = Graph.from_template(
                id_=self._id_gen.new_graph_id(),
                task_id=event.task_id,
                template=template,
                node_id_factory=self._id_gen.new_node_id,
                now=now,
            )
            await uow.graphs.save(graph)
            uow.stage_events(graph.pull_events())
            await uow.commit()

        self._logger.info(
            "Graph built for task",
            task_id=event.task_id.value,
            graph_id=graph.id.value,
        )
