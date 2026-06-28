from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.events.graph_execution_created_event import (
    GraphExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
    GraphExecutionState,
)
from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
    GraphExecutionStateId,
)
from shell.domain.execution.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class GraphExecutionCreatedHandler:
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

    async def handle(self, graph_execution_created_event: GraphExecutionCreatedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            graph_execution = await unit_of_work.graph_execution_repository.get_by_id(graph_execution_created_event.graph_execution_id)
            if graph_execution is None:
                self._logger.warning(
                    "graph_execution_created_handler.graph_not_found",
                    graph_execution_id=graph_execution_created_event.graph_execution_id.value,
                )
                return

            task_execution = await unit_of_work.task_execution_repository.get_by_id(
                graph_execution.task_execution_id,
            )
            if task_execution is None:
                self._logger.warning(
                    "graph_execution_created_handler.task_not_found",
                    task_execution_id=graph_execution.task_execution_id.value,
                )
                return

            now = self._clock.now()

            if graph_execution.parent_graph_execution_id is None:
                can_continue = task_execution.increment_cycle()
                if not can_continue:
                    task_execution.exhaust(now)
                    await unit_of_work.task_execution_repository.save(task_execution)
                    unit_of_work.stage_events(task_execution.pull_events())
                    return

                if graph_execution_created_event.goal:
                    state = GraphExecutionState.create(
                        id_=GraphExecutionStateId.generate(),
                        graph_execution_id=graph_execution.id,
                        direction=StateDirection.IN,
                        now=now,
                    )
                    state.patch({"goal": graph_execution_created_event.goal})
                    await unit_of_work.graph_execution_state_repository.save(state)
                    unit_of_work.stage_events(state.pull_events())

                task_execution.start(now)
                await unit_of_work.task_execution_repository.save(task_execution)
                unit_of_work.stage_events(task_execution.pull_events())
