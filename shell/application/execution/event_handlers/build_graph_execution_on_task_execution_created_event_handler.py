from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.platform.exceptions import GraphDefinitionNotFoundException
from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_constructed_event import (
    GraphExecutionConstructedEvent,
)
from shell.domain.execution.ports.graph_execution_definition_provider import (
    GraphExecutionDefinitionProvider,
)
from shell.domain.platform.events import DomainEvent
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


class BuildGraphExecutionOnTaskExecutionCreatedEventHandler:
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

    async def handle(self, task_execution_created_event: TaskExecutionCreatedEvent) -> None:
        now = self._clock.now()

        graph_definition = await self._definition_provider.get_graph_definition_by_name(
            self._name,
        )
        if graph_definition is None:
            raise GraphDefinitionNotFoundException(
                f"GraphDefinition {self._name!r} not found",
            )

        async with self._unit_of_work as unit_of_work:
            existing = await unit_of_work.graph_execution_repository.get_by_task_execution_id(
                task_execution_created_event.task_execution_id
            )
            if existing is not None:
                self._logger.info(
                    "Graph already exists for task — skipping build",
                    task_execution_id=task_execution_created_event.task_execution_id.value,
                )
                return

            from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
                GraphNodeExecution as GNE,
            )

            graph_execution_id = self._id_generator.new_graph_execution_id()
            events: list[DomainEvent] = []
            for node_def in graph_definition.graph_node_execution_definitions:
                node_id = self._id_generator.new_graph_node_execution_id()
                node = GNE(
                    id=node_id,
                    graph_execution_id=graph_execution_id,
                    position=node_def.position,
                    mode=Mode(node_def.mode),
                    role=node_def.role,
                    node_type=node_def.node_type,
                    remaining_retries=node_def.retries,
                    retry_delay_seconds=0,
                    timeout_seconds=node_def.timeout,
                )
                await unit_of_work.graph_node_execution_repository.save(node)

            graph_execution = GraphExecution(
                id=graph_execution_id,
                task_execution_id=task_execution_created_event.task_execution_id,
            )
            await unit_of_work.graph_execution_repository.save(graph_execution)
            events.append(
                GraphExecutionConstructedEvent.now(
                    graph_execution_id=graph_execution.id,
                    task_execution_id=task_execution_created_event.task_execution_id,
                    now=now,
                )
            )
            unit_of_work.stage_events(events)

        self._logger.info(
            "Graph built for task",
            task_execution_id=task_execution_created_event.task_execution_id.value,
            graph_execution_id=graph_execution.id.value,
        )
