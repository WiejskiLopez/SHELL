from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
    GraphExecutionState,
)
from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
    GraphExecutionStateId,
)
from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.graph_execution_state.repositories.graph_execution_state_repository import (
    GraphExecutionStateRepository,
)
from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.platform.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution.events.graph_execution_created_event import (
        GraphExecutionCreatedEvent,
    )
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock


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
            graph_execution = await unit_of_work.repository(GraphExecutionRepository).get_by_id(graph_execution_created_event.graph_execution_id)

            task_execution = await unit_of_work.repository(TaskExecutionRepository).get_by_id(
                graph_execution.task_execution_id,
            )

            now = self._clock.now()

            if graph_execution.parent_graph_execution_id is None:
                can_continue = task_execution.increment_cycle()
                if not can_continue:
                    task_execution.exhaust(now)
                    await unit_of_work.repository(TaskExecutionRepository).save(task_execution)
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
                    await unit_of_work.repository(GraphExecutionStateRepository).save(state)
                    unit_of_work.stage_events(state.pull_events())

                task_execution.start(now)
                await unit_of_work.repository(TaskExecutionRepository).save(task_execution)
                unit_of_work.stage_events(task_execution.pull_events())
