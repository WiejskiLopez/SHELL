"""GraphExecutionCreatedTaskExecutionCycleHandler — manages TaskExecution cycle.

Subscribes to GraphExecutionCreatedEvent. For top-level graphs (no parent),
increments the planning cycle on TaskExecution and starts it if cycles remain.
Modyfikuje tylko TaskExecution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution.events.graph_execution_created_event import (
        GraphExecutionCreatedEvent,
    )
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock


class GraphExecutionCreatedTaskExecutionCycleHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        logger: Logger,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._logger = logger

    async def handle(
        self, graph_execution_created_event: GraphExecutionCreatedEvent
    ) -> None:
        async with self._unit_of_work as unit_of_work:
            graph_execution = await unit_of_work.repository(
                GraphExecutionRepository
            ).get_by_id(graph_execution_created_event.graph_execution_id)
            if graph_execution is None or graph_execution.parent_graph_execution_id is not None:
                return

            task_execution = await unit_of_work.repository(
                TaskExecutionRepository
            ).get_by_id(graph_execution_created_event.task_execution_id)
            if task_execution is None:
                self._logger.warning(
                    "graph_execution_created_task_execution_cycle_handler.task_not_found",
                    task_execution_id=graph_execution_created_event.task_execution_id.value,
                )
                return

            now = self._clock.now()
            can_continue = task_execution.increment_cycle()
            if not can_continue:
                task_execution.exhaust(now)
                await unit_of_work.repository(TaskExecutionRepository).save(task_execution)
                unit_of_work.stage_events(task_execution.pull_events())
                return

            task_execution.start(now)
            await unit_of_work.repository(TaskExecutionRepository).save(task_execution)
            unit_of_work.stage_events(task_execution.pull_events())
