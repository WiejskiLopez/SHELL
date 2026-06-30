"""GraphExecutionFailedHandler — reacts to GraphExecution failure.

Two mutually exclusive paths:
1. If task can't continue (exhausted): modifies **only** TaskExecution.
2. If task can continue: creates a new GraphExecution (replan) — modifies
   **only** GraphExecution. The cycle increment on TaskExecution is handled
   by ``GraphExecutionCreatedTaskExecutionCycleHandler`` reacting to the
   ``GraphExecutionCreatedEvent`` from the replan graph.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.value_objects.goal import Goal
from shell.domain.execution.value_objects.graph_depth import GraphDepth
from shell.domain.execution.value_objects.ids import GraphExecutionId
from shell.domain.execution.value_objects.max_subgraph_depth import MaxSubgraphDepth

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution.events.graph_execution_failed_event import (
        GraphExecutionFailedEvent,
    )
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock


class GraphExecutionFailedHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
        logger: Logger,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator
        self._logger = logger

    async def handle(self, graph_execution_failed_event: GraphExecutionFailedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            graph_execution = await unit_of_work.repository(GraphExecutionRepository).get_by_id(
                graph_execution_failed_event.graph_execution_id
            )
            if graph_execution is None:
                self._logger.warning(
                    "graph_execution_failed_handler.graph_execution_not_found",
                    graph_execution_id=graph_execution_failed_event.graph_execution_id.value,
                )
                return

            if graph_execution.parent_graph_execution_id is not None:
                return

            task_execution = await unit_of_work.repository(TaskExecutionRepository).get_by_id(
                graph_execution.task_execution_id,
            )
            if task_execution is None:
                self._logger.warning(
                    "graph_execution_failed_handler.task_execution_not_found",
                    task_execution_id=graph_execution.task_execution_id.value,
                )
                return

            now = self._clock.now()
            if task_execution.current_cycle >= task_execution.max_planning_cycles:
                task_execution.exhaust(now)
                await unit_of_work.repository(TaskExecutionRepository).save(task_execution)
                unit_of_work.stage_events(task_execution.pull_events())
                return

            replan_goal = Goal(f"replan: {graph_execution.task_execution_id.value} - {graph_execution_failed_event.reason}")
            new_graph = GraphExecution.create_main_round(
                id_=self._id_generator.new_id(GraphExecutionId),
                task_execution_id=graph_execution.task_execution_id,
                depth=GraphDepth(0),
                max_subgraph_depth=MaxSubgraphDepth(5),
            )
            new_graph.emit_created_event(goal=replan_goal, now=now)
            await unit_of_work.repository(GraphExecutionRepository).save(new_graph)
            unit_of_work.stage_events(new_graph.pull_events())
