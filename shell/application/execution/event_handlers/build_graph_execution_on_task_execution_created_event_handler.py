from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.definition.exceptions.graph_definition_not_found_exception import (
    GraphDefinitionNotFoundException,
)
from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.ports.graph_definition_semantic_query import (
    GraphDefinitionSemanticQuery,
)
from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.value_objects.graph_definition_id import GraphDefinitionIdRef
from shell.domain.execution.value_objects.graph_node_definition_id import GraphNodeDefinitionId
from shell.domain.execution.value_objects.ids import GraphExecutionId

if TYPE_CHECKING:
    from shell.application.platform.ports.ports import (
        Clock,
        IdGenerator,
        Logger,
        UnitOfWork,
    )
    from shell.domain.execution.aggregates.graph_execution.ports.graph_execution_definition_provider import (
        GraphExecutionDefinitionProvider,
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

        query = GraphDefinitionSemanticQuery(
            text=self._name,
            purpose="planning",
            default_graph_definition="PLANNER",
        )
        graph_definition = await self._definition_provider.get_graph_definition_by_semantic_name(
            query,
        )
        if graph_definition is None:
            raise GraphDefinitionNotFoundException(
                f"GraphDefinition {self._name!r} not found",
            )

        async with self._unit_of_work as unit_of_work:
            existing = await unit_of_work.repository(
                GraphExecutionRepository
            ).get_by_task_execution_id(task_execution_created_event.task_execution_id)
            if existing is not None:
                self._logger.info(
                    "Graph already exists for task — skipping build",
                    task_execution_id=task_execution_created_event.task_execution_id.value,
                )
                return

            graph_execution_id = self._id_generator.new_id(GraphExecutionId)
            graph_node_definition_ids = [
                GraphNodeDefinitionId.generate()
                for _ in graph_definition.graph_node_execution_definitions
            ]

            graph_execution = GraphExecution.initialize(
                id_=graph_execution_id,
                task_execution_id=task_execution_created_event.task_execution_id,
                graph_definition_id=GraphDefinitionIdRef(graph_definition.id),
                graph_node_definition_ids=graph_node_definition_ids,
                now=now,
            )
            await unit_of_work.repository(GraphExecutionRepository).save(graph_execution)
            unit_of_work.stage_events(graph_execution.pull_events())

        self._logger.info(
            "Graph built for task",
            task_execution_id=task_execution_created_event.task_execution_id.value,
            graph_execution_id=graph_execution.id.value,
        )
