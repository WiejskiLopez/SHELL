from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_failed_event import (
    GraphExecutionFailedEvent,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


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
            graph_execution = await unit_of_work.graph_execution_repository.get_by_id(graph_execution_failed_event.graph_execution_id)
            if graph_execution is None:
                self._logger.warning(
                    "graph_execution_failed_handler.graph_not_found",
                    graph_execution_id=graph_execution_failed_event.graph_execution_id.value,
                )
                return

            if graph_execution.parent_graph_execution_id is not None:
                return

            task_execution = await unit_of_work.task_execution_repository.get_by_id(
                graph_execution.task_execution_id,
            )
            if task_execution is None:
                self._logger.warning(
                    "graph_execution_failed_handler.task_not_found",
                    task_execution_id=graph_execution.task_execution_id.value,
                )
                return

            now = self._clock.now()
            can_continue = task_execution.increment_cycle()
            if not can_continue:
                task_execution.exhaust(now)
                await unit_of_work.task_execution_repository.save(task_execution)
                unit_of_work.stage_events(task_execution.pull_events())
                return

            replan_goal = f"replan: {graph_execution.task_execution_id.value} - {graph_execution_failed_event.reason}"
            new_graph = GraphExecution.create_main_round(
                id_=self._id_generator.new_graph_execution_id(),
                task_execution_id=graph_execution.task_execution_id,
            )
            from shell.domain.execution.aggregates.graph_execution.events.graph_execution_created_event import (
                GraphExecutionCreatedEvent,
            )

            new_graph.append_event(
                GraphExecutionCreatedEvent.now(
                    graph_execution_id=new_graph.id,
                    task_execution_id=graph_execution.task_execution_id,
                    now=now,
                    goal=replan_goal,
                    depth=0,
                ),
            )
            await unit_of_work.graph_execution_repository.save(new_graph)
            await unit_of_work.task_execution_repository.save(task_execution)
            unit_of_work.stage_events(new_graph.pull_events())
            unit_of_work.stage_events(task_execution.pull_events())
