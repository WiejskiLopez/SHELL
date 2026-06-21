"""BuildGraphExecutionOnTaskExecutionCreatedEvent — reacts to TaskExecutionCreatedEvent and builds a Graph.

The Task aggregate is intentionally agnostic of which Graph realises it.
This handler bridges that gap: when a Task is created, it materialises a
Graph from a GraphDefinition (default name: ``base_planner``), persists it
in its own transactional boundary, and forwards the resulting domain
events (``GraphExecutionBuiltEvent``) downstream.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.platform.exceptions import GraphDefinitionNotFoundException
from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.ports.graph_execution_definition_provider import (  # noqa: TC002 — GraphExecutionDefinitionProvider używany w konstruktorze handlera
    GraphExecutionDefinitionProvider,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.ports import (
        Clock,
        IdGenerator,
        Logger,
        UnitOfWork,
    )
    from shell.domain.execution.events import TaskExecutionCreatedEvent


GRAPH_DEFINITION_NAME = "base_planner"


class BuildGraphExecutionOnTaskExecutionCreatedEvent:
    """Event handler — listens to ``TaskExecutionCreatedEvent`` and builds a Graph."""

    def __init__(
        self,
        uow: UnitOfWork,
        definition_provider: GraphExecutionDefinitionProvider,
        clock: Clock,
        id_gen: IdGenerator,
        logger: Logger,
        name: str = GRAPH_DEFINITION_NAME,
    ) -> None:
        self._uow = uow
        self._definition_provider = definition_provider
        self._clock = clock
        self._id_gen = id_gen
        self._logger = logger
        self._name = name

    async def handle(self, event: TaskExecutionCreatedEvent) -> None:
        now = self._clock.now()

        graph_definition = await self._definition_provider.get_graph_definition_by_name(
            self._name,
        )
        if graph_definition is None:
            raise GraphDefinitionNotFoundException(
                f"GraphDefinition {self._name!r} not found",
            )

        async with self._uow as uow:
            existing = await uow.graph_executions.get_by_task_execution_id(event.task_execution_id)
            if existing is not None:
                self._logger.info(
                    "Graph already exists for task — skipping build",
                    task_execution_id=event.task_execution_id.value,
                )
                return

            from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import GraphNodeExecution

            node_ids: list = []
            for node_def in graph_definition.graph_node_execution_definitions:
                node_id = self._id_gen.new_graph_node_execution_id()
                node = GraphNodeExecution.from_node_definition(
                    id_=node_id,
                    node_def=node_def,
                )
                await uow.graph_node_executions.save(node)
                node_ids.append(node_id)

            graph_execution_id = self._id_gen.new_graph_execution_id()
            graph_execution = GraphExecution.from_graph_definition(
                id_=graph_execution_id,
                task_execution_id=event.task_execution_id,
                graph_definition=graph_definition,
                node_ids=node_ids,
                id_gen=self._id_gen,
                now=now,
            )
            await uow.graph_executions.save(graph_execution)
            uow.stage_events(graph_execution.pull_events())

        self._logger.info(
            "Graph built for task",
            task_execution_id=event.task_execution_id.value,
            graph_execution_id=graph_execution.id.value,
        )
