from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
    TaskExecutionState,
)
from shell.domain.execution.aggregates.workflow.events.workflow_completed_event import (
    WorkflowCompletedEvent,
)
from shell.domain.execution.value_objects.state_data import StateData
from shell.domain.execution.value_objects.state_direction import StateDirection
from shell.domain.platform.value_objects.created_at import CreatedAt

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
            workflow_states = await unit_of_work.workflow_state_repository.list_by_workflow_id_and_direction(
                workflow.id, StateDirection.OUT
            )
            output_payload: dict[str, Any] = {
                "workflow_id": workflow_completed_event.workflow_id.value,
                "state_outputs": [s.state_data.to_dict() for s in workflow_states],
            }
            state = TaskExecutionState.create(
                id_=self._id_generator.new_task_execution_state_id(),
                task_execution_id=task_execution.id,
                direction=StateDirection.IN,
                state_data=StateData(output_payload),
                now=CreatedAt.from_datetime(now),
            )
            await unit_of_work.task_execution_state_repository.save(state)
            unit_of_work.stage_events(state.pull_events())
