from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.task_execution.events.task_execution_completed_event import (
    TaskExecutionCompletedEvent,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class TaskExecutionCompletedPropagateOutputHandler:
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

    async def handle(self, event: TaskExecutionCompletedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            task_execution = await unit_of_work.task_executions.get_by_id(event.task_execution_id)
            if task_execution is None or task_execution.workflow_id is None:
                self._logger.warning(
                    "task_execution_completed_propagate_output_handler.task_not_found",
                    task_execution_id=event.task_execution_id.value,
                )
                return

            workflow = await unit_of_work.workflows.get_by_id(task_execution.workflow_id)
            if workflow is None:
                self._logger.warning(
                    "task_execution_completed_propagate_output_handler.workflow_not_found",
                    workflow_id=task_execution.workflow_id.value,
                )
                return

            now = self._clock.now()
            output_payload: dict[str, Any] = {
                "task_execution_id": event.task_execution_id.value,
                "task_execution_name": event.task_execution_name.value,
                "output": event.output,
            }
            workflow.add_state_input(output_payload, now)
            await unit_of_work.workflows.save(workflow)
            unit_of_work.stage_events(workflow.pull_events())
