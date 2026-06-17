"""BuildGraphOnTaskExecutionCreated — reacts to TaskExecutionCreated and builds a Graph.

The Task aggregate is intentionally agnostic of which Graph realises it.
This handler bridges that gap: when a Task is created, it materialises a
Graph from a GraphDefinition (default name: ``base_planner``), persists it
in its own transactional boundary, and forwards the resulting domain
events (``GraphBuilt``) downstream.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.exceptions import GraphDefinitionNotFoundException
from shell.domain.entities.graph import Graph

if TYPE_CHECKING:
    from shell.application.ports.ports import (
        Clock,
        IdGenerator,
        Logger,
        UnitOfWork,
    )
    from shell.domain.events.events import TaskExecutionCreated


GRAPH_DEFINITION_NAME = "base_planner"


class BuildGraphOnTaskExecutionCreated:
    """Event handler — listens to ``TaskExecutionCreated`` and builds a Graph."""

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        logger: Logger,
        name: str = GRAPH_DEFINITION_NAME,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._logger = logger
        self._name = name

    async def handle(self, event: TaskExecutionCreated) -> None:
        self._logger.info(
            "Handle TaskExecutionCreated:",
            task_execution_id=event.task_execution_id.value,
        )
        now = self._clock.now()
        async with self._uow as uow:
            existing = await uow.graphs.get_by_task_execution_id(event.task_execution_id)
            if existing is not None:
                self._logger.info(
                    "Graph already exists for task — skipping build",
                    task_execution_id=event.task_execution_id.value,
                )
                return

            graph_definition = await uow.graph_definitions.get_graph_definition_by_name(
                self._name,
            )
            if graph_definition is None:
                raise GraphDefinitionNotFoundException(
                    f"GraphDefinition {self._name!r} not found",
                )

            graph = Graph.from_graph_definition(
                id_=self._id_gen.new_graph_id(),
                task_execution_id=event.task_execution_id,
                graph_definition=graph_definition,
                node_id_factory=self._id_gen.new_node_id,
                now=now,
            )
            await uow.graphs.save(graph)
            uow.stage_events(graph.pull_events())
            await uow.commit()

        self._logger.info(
            "Graph built for task",
            task_execution_id=event.task_execution_id.value,
            graph_id=graph.id.value,
        )
