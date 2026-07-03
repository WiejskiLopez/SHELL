from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution_state.repositories.task_execution_state_repository import (
    TaskExecutionStateRepository,
)
from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
    TaskExecutionState,
)
from shell.domain.execution.value_objects.ids import TaskExecutionStateId
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.state_data import StateData
from shell.domain.platform.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.events.event import (
        GraphExecutionCompletedEvent,
    )

    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock


class PropagateGraphOutputToTaskInput:
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
                    "propagate_graph_output_to_task_input.graph_not_found",
                    graph_execution_id=event.graph_execution_id.value,
                )
                return

            if graph_execution.parent_graph_execution_id is not None:
                return

            task_execution = await unit_of_work.repository(TaskExecutionRepository).get_by_id(
                graph_execution.task_execution_id
            )
            if task_execution is None:
                self._logger.warning(
                    "propagate_graph_output_to_task_input.task_not_found",
                    task_execution_id=graph_execution.task_execution_id.value,
                )
                return

            now = self._clock.now()
            output_payload: dict[str, Any] = {
                "graph_execution_id": event.graph_execution_id.value,
                "verifier_result": event.verifier_result,
            }
            state = TaskExecutionState.create(
                id_=self._id_generator.new_id(TaskExecutionStateId),
                task_execution_id=task_execution.id,
                direction=StateDirection.IN,
                state_data=StateData(output_payload),
                now=CreatedAt.from_datetime(now),
            )
            await unit_of_work.repository(TaskExecutionStateRepository).save(state)
            unit_of_work.stage_events(state.pull_events())
