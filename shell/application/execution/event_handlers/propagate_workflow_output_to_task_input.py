from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution_state.repositories.task_execution_state_repository import (
    TaskExecutionStateRepository,
)
from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
    TaskExecutionState,
)
from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.aggregates.workflow_state.repositories.workflow_state_repository import (
    WorkflowStateRepository,
)
from shell.domain.execution.value_objects.ids import TaskExecutionStateId
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.state_data import StateData
from shell.domain.platform.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow.events import (
        WorkflowCompletedEvent,
    )

    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock


class PropagateWorkflowOutputToTaskInput:
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

    async def handle(self, event: WorkflowCompletedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            task_execution_id = event.task_execution_id
            if task_execution_id is None:
                self._logger.warning(
                    "propagate_workflow_output_to_task_input.task_execution_id_missing",
                )
                return

            task_execution = await unit_of_work.repository(TaskExecutionRepository).get_by_id(
                task_execution_id
            )
            if task_execution is None:
                self._logger.warning(
                    "propagate_workflow_output_to_task_input.task_not_found",
                    task_execution_id=task_execution_id.value,
                )
                return

            workflow = await unit_of_work.repository(WorkflowRepository).get_by_id(
                event.workflow_id
            )
            if workflow is None:
                self._logger.warning(
                    "propagate_workflow_output_to_task_input.workflow_not_found",
                    workflow_id=event.workflow_id.value,
                )
                return

            now = self._clock.now()
            workflow_states = await unit_of_work.repository(
                WorkflowStateRepository
            ).list_by_workflow_id_and_direction(workflow.id, StateDirection.OUT)
            output_payload: dict[str, Any] = {
                "workflow_id": event.workflow_id.value,
                "state_outputs": [s.state_data.to_dict() for s in workflow_states],
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
