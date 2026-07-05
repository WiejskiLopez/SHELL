"""WorkflowStartedAttachTaskExecutionHandler — attaches TaskExecution to Workflow.

Subscribes to WorkflowStartedEvent. Loads the TaskExecution, prepares workspace,
links it to the Workflow via ``execute_in_workflow``, and persists.
Modyfikuje tylko TaskExecution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow.events import (
        WorkflowStartedEvent,
    )

    from shell.application.platform.ports.ports import Logger, UnitOfWork


class WorkflowStartedAttachTaskExecutionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        logger: Logger,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._logger = logger

    async def handle(self, event: WorkflowStartedEvent) -> None:
        if event.task_execution_id is None:
            self._logger.warning(
                "workflow_started_attach_task_execution_handler.missing_task_execution_id",
                workflow_id=event.workflow_id.value,
            )
            return

        async with self._unit_of_work as unit_of_work:
            task_execution = await unit_of_work.repository(
                TaskExecutionRepository
            ).get_by_id(event.task_execution_id)
            if task_execution is None:
                self._logger.warning(
                    "workflow_started_attach_task_execution_handler.task_not_found",
                    task_execution_id=event.task_execution_id.value,
                )
                return

            if event.work_dir:
                task_execution.prepare_workspace(event.work_dir)

            task_execution.execute_in_workflow(event.workflow_id)
            await unit_of_work.repository(TaskExecutionRepository).save(task_execution)
            unit_of_work.stage_events(task_execution.pull_events())
