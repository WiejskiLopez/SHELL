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


class PropagateTaskOutputToWorkflowInput:
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

    async def handle(self, event: TaskExecutionCompletedEvent) -> None:
        async with self._uow as uow:
            task_execution = await uow.task_executions.get_by_id(event.task_execution_id)
            if task_execution is None or task_execution.workflow_id is None:
                self._logger.warning(
                    "propagate_task_output_to_workflow_input.task_not_found",
                    task_execution_id=event.task_execution_id.value,
                )
                return

            workflow = await uow.workflows.get_by_id(task_execution.workflow_id)
            if workflow is None:
                self._logger.warning(
                    "propagate_task_output_to_workflow_input.workflow_not_found",
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
            await uow.workflows.save(workflow)
            uow.stage_events(workflow.pull_events())
