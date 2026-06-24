"""BuildGraphExecutionOnTaskExecutionCreatedEvent — reacts to TaskExecutionCreatedEvent and builds a Graph.

The Task aggregate is intentionally agnostic of which Graph realises it.
This handler bridges that gap: when a Task is created, it materialises a
Graph from a GraphDefinition (default name: ``base_planner``), persists it
in its own transactional boundary, and forwards the resulting domain
events (``GraphExecutionBuiltEvent``) downstream.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.application.platform.exceptions import GraphDefinitionNotFoundException
from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.ports.graph_execution_definition_provider import (
    GraphExecutionDefinitionProvider,  # noqa: TC002 — GraphExecutionDefinitionProvider używany w konstruktorze handlera
)
from shell.domain.platform.value_objects.mode import Mode

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
        unit_of_work: UnitOfWork,
        definition_provider: GraphExecutionDefinitionProvider,
        clock: Clock,
        id_generator: IdGenerator,
        logger: Logger,
        name: str = GRAPH_DEFINITION_NAME,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._definition_provider = definition_provider
        self._clock = clock
        self._id_generator = id_generator
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

        async with self._unit_of_work as unit_of_work:
            existing = await unit_of_work.graph_executions.get_by_task_execution_id(event.task_execution_id)
            if existing is not None:
                self._logger.info(
                    "Graph already exists for task — skipping build",
                    task_execution_id=event.task_execution_id.value,
                )
                return

            from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
                GraphNodeExecution,
            )

            node_ids: list[Any] = []
            for node_def in graph_definition.graph_node_execution_definitions:
                node_id = self._id_generator.new_graph_node_execution_id()
                node = GraphNodeExecution(
                    id=node_id,
                    position=node_def.position,
                    mode=Mode(node_def.mode),
                    role=node_def.role,
                    node_type=node_def.node_type,
                    model=node_def.model,
                    command=node_def.command,
                    timeout=node_def.timeout,
                    retries=node_def.retries,
                    log_level=node_def.log_level,
                    max_step=node_def.max_step or 0,
                    no_ask_user=node_def.no_ask_user,
                    autopilot=node_def.autopilot,
                    status_initial=node_def.status_initial,
                    timeout_seconds=node_def.timeout,
                    max_retries=node_def.retries,
                )
                await unit_of_work.graph_node_executions.save(node)
                node_ids.append(node_id)

            graph_execution_id = self._id_generator.new_graph_execution_id()
            graph_execution = GraphExecution.from_graph_definition(
                id_=graph_execution_id,
                task_execution_id=event.task_execution_id,
                graph_definition=graph_definition,
                node_ids=node_ids,
                id_generator=self._id_generator,
                now=now,
            )
            await unit_of_work.graph_executions.save(graph_execution)
            unit_of_work.stage_events(graph_execution.pull_events())

        self._logger.info(
            "Graph built for task",
            task_execution_id=event.task_execution_id.value,
            graph_execution_id=graph_execution.id.value,
        )
