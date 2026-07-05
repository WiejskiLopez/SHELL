from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.aggregates.workflow_state.repositories.workflow_state_repository import (
    WorkflowStateRepository,
)
from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
    WorkflowStateId,
)
from shell.domain.execution.aggregates.workflow_state.workflow_state import (
    WorkflowState,
)
from shell.domain.platform.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.task_execution.events import (
        TaskExecutionCompletedEvent,
    )
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock


class PropagateTaskOutputToWorkflowInput:
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
            task_execution = await unit_of_work.repository(TaskExecutionRepository).get_by_id(
                event.task_execution_id
            )
            if task_execution is None or task_execution.workflow_id is None:
                self._logger.warning(
                    "propagate_task_output_to_workflow_input.task_not_found",
                    task_execution_id=event.task_execution_id.value,
                )
                return

            workflow = await unit_of_work.repository(WorkflowRepository).get_by_id(
                task_execution.workflow_id
            )
            if workflow is None:
                self._logger.warning(
                    "propagate_task_output_to_workflow_input.workflow_not_found",
                    workflow_id=task_execution.workflow_id.value,
                )
                return

            now = self._clock.now()
            output_payload: dict[str, Any] = {
                "task_execution_id": event.task_execution_id.value,
            }
            state = WorkflowState.create(
                id_=self._id_generator.new_id(WorkflowStateId),
                workflow_id=workflow.id,
                direction=StateDirection.IN,
                payload=output_payload,
                now=now,
            )
            await unit_of_work.repository(WorkflowStateRepository).save(state)
            unit_of_work.stage_events(state.pull_events())
