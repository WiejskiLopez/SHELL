from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_execution.events.graph_execution_completed_event import (
    GraphExecutionCompletedEvent,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class PropagateGraphOutputToTaskInput:
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

    async def handle(self, event: GraphExecutionCompletedEvent) -> None:
        async with self._uow as uow:
            graph_execution = await uow.graph_executions.get_by_id(event.graph_execution_id)
            if graph_execution is None:
                self._logger.warning(
                    "propagate_graph_output_to_task_input.graph_not_found",
                    graph_execution_id=event.graph_execution_id.value,
                )
                return

            if graph_execution.parent_graph_execution_id is not None:
                return

            task_execution = await uow.task_executions.get_by_id(
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
            task_execution.add_state_input(output_payload, now)
            await uow.task_executions.save(task_execution)
            uow.stage_events(task_execution.pull_events())
