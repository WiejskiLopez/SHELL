from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.workflow.events.workflow_completed_event import (
    WorkflowCompletedEvent,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class WorkflowCompletedPropagateOutputHandler:
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

    async def handle(self, event: WorkflowCompletedEvent) -> None:
        async with self._uow as uow:
            task_execution = await uow.task_executions.get_by_id(event.task_execution_id)
            if task_execution is None:
                self._logger.warning(
                    "workflow_completed_propagate_output_handler.task_not_found",
                    task_execution_id=event.task_execution_id.value,
                )
                return

            workflow = await uow.workflows.get_by_id(event.workflow_id)
            if workflow is None:
                self._logger.warning(
                    "workflow_completed_propagate_output_handler.workflow_not_found",
                    workflow_id=event.workflow_id.value,
                )
                return

            now = self._clock.now()
            output_payload: dict[str, Any] = {
                "workflow_id": event.workflow_id.value,
                "state_outputs": [s.payload for s in workflow.state_outputs],
            }
            task_execution.add_state_input(output_payload, now)
            await uow.task_executions.save(task_execution)
            uow.stage_events(task_execution.pull_events())
