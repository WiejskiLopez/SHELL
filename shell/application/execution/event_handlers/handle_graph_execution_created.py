from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.events.graph_execution_created_event import (
    GraphExecutionCreatedEvent,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class HandleGraphExecutionCreated:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        logger: Logger,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._logger = logger

    async def handle(self, event: GraphExecutionCreatedEvent) -> None:
        async with self._uow as uow:
            graph_execution = await uow.graph_executions.get_by_id(event.graph_execution_id)
            if graph_execution is None:
                self._logger.warning(
                    "handle_graph_execution_created.graph_not_found",
                    graph_execution_id=event.graph_execution_id.value,
                )
                return

            task_execution = await uow.task_executions.get_by_id(
                graph_execution.task_execution_id,
            )
            if task_execution is None:
                self._logger.warning(
                    "handle_graph_execution_created.task_not_found",
                    task_execution_id=graph_execution.task_execution_id.value,
                )
                return

            now = self._clock.now()

            if graph_execution.parent_graph_execution_id is None:
                can_continue = task_execution.increment_cycle()
                if not can_continue:
                    task_execution.exhaust(now)
                    await uow.task_executions.save(task_execution)
                    uow.stage_events(task_execution.pull_events())
                    return

                if event.goal:
                    graph_execution.add_state_input({"goal": event.goal}, now)

                task_execution.start(now)
                await uow.task_executions.save(task_execution)
                uow.stage_events(task_execution.pull_events())
