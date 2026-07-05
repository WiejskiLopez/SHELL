from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.value_objects.task_execution_status import TaskExecutionStatus

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution.events import (
        GraphExecutionCompletedEvent,
    )
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock


class GraphExecutionCompletedHandler:
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

    async def handle(self, event: GraphExecutionCompletedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            graph_execution = await unit_of_work.repository(GraphExecutionRepository).get_by_id(
                event.graph_execution_id
            )
            if graph_execution is None:
                self._logger.warning(
                    "graph_execution_completed_handler.graph_execution_not_found",
                    graph_execution_id=event.graph_execution_id.value,
                )
                return

            if graph_execution.parent_graph_execution_id is not None:
                return

            task_execution = await unit_of_work.repository(TaskExecutionRepository).get_by_id(
                graph_execution.task_execution_id,
            )
            if task_execution is None:
                self._logger.warning(
                    "graph_execution_completed_handler.task_execution_not_found",
                    task_execution_id=graph_execution.task_execution_id.value,
                )
                return

            if task_execution.status != TaskExecutionStatus.IN_PROGRESS:
                self._logger.warning(
                    "graph_execution_completed_handler.task_not_in_progress",
                    task_execution_id=graph_execution.task_execution_id.value,
                    status=task_execution.status.value,
                )
                return

            now = self._clock.now()
            task_execution.complete(now=now)
            await unit_of_work.repository(TaskExecutionRepository).save(task_execution)
            unit_of_work.stage_events(task_execution.pull_events())
