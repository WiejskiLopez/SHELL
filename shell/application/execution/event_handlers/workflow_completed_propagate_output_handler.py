from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.workflow.events.workflow_completed_event import (
    WorkflowCompletedEvent,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class WorkflowCompletedPropagateOutputHandler:
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

    async def handle(self, workflow_completed_event: WorkflowCompletedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            task_execution = await unit_of_work.task_execution_repository.get_by_id(workflow_completed_event.task_execution_id)
            if task_execution is None:
                self._logger.warning(
                    "workflow_completed_propagate_output_handler.task_not_found",
                    task_execution_id=workflow_completed_event.task_execution_id.value,
                )
                return

            workflow = await unit_of_work.workflow_repository.get_by_id(workflow_completed_event.workflow_id)
            if workflow is None:
                self._logger.warning(
                    "workflow_completed_propagate_output_handler.workflow_not_found",
                    workflow_id=workflow_completed_event.workflow_id.value,
                )
                return

            now = self._clock.now()
            output_payload: dict[str, Any] = {
                "workflow_id": workflow_completed_event.workflow_id.value,
                "state_outputs": [s.payload for s in workflow.state_outputs],
            }
            task_execution.add_state_input(output_payload, now)
            await unit_of_work.task_execution_repository.save(task_execution)
            unit_of_work.stage_events(task_execution.pull_events())
