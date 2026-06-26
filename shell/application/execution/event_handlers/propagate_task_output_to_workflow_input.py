from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.task_execution.events.task_execution_completed_event import (
    TaskExecutionCompletedEvent,
)
from shell.domain.execution.aggregates.workflow_state.workflow_state import (
    WorkflowState,
)
from shell.domain.execution.value_objects.state_data import StateData
from shell.domain.execution.value_objects.state_kind import StateKind
from shell.domain.platform.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


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

    async def handle(self, task_execution_completed_event: TaskExecutionCompletedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            task_execution = await unit_of_work.task_execution_repository.get_by_id(task_execution_completed_event.task_execution_id)
            if task_execution is None or task_execution.workflow_id is None:
                self._logger.warning(
                    "propagate_task_output_to_workflow_input.task_not_found",
                    task_execution_id=task_execution_completed_event.task_execution_id.value,
                )
                return

            workflow = await unit_of_work.workflow_repository.get_by_id(task_execution.workflow_id)
            if workflow is None:
                self._logger.warning(
                    "propagate_task_output_to_workflow_input.workflow_not_found",
                    workflow_id=task_execution.workflow_id.value,
                )
                return

            now = self._clock.now()
            output_payload: dict[str, Any] = {
                "task_execution_id": task_execution_completed_event.task_execution_id.value,
                "task_execution_name": task_execution_completed_event.task_execution_name.value,
                "output": task_execution_completed_event.output,
            }
            state = WorkflowState.create(
                id_=self._id_generator.new_workflow_state_id(),
                workflow_id=workflow.id,
                kind=StateKind.INPUT,
                payload=output_payload,
                now=now,
            )
            await unit_of_work.workflow_state_repository.save(state)
            unit_of_work.stage_events(state.pull_events())
