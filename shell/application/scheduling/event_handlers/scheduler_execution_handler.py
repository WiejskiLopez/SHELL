from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.events import (
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.scheduling.services.scheduler_orchestrator import (
        SchedulerOrchestrator,
    )


class SchedulerExecutionHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        logger: Logger,
        orchestrator: SchedulerOrchestrator,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._logger = logger
        self._orchestrator = orchestrator

    async def handle_workflow_completed(
        self, event: WorkflowCompletedEvent
    ) -> None:
        now = self._clock.now()
        async with self._uow as uow:
            executions = await uow.scheduler_executions.get_by_action_ref(
                event.workflow_id.value,
            )
            if not executions:
                self._logger.info(
                    "scheduler_execution_handler.no_matching_execution",
                    workflow_id=event.workflow_id.value,
                )
                return

            for execution in executions:
                if execution.status.value != "executing":
                    continue

                events = self._orchestrator.complete_execution(
                    execution,
                    output_state={},
                    error=None,
                    now=now,
                )
                await uow.scheduler_executions.save(execution)
                uow.stage_events(events)

            await uow.commit()

            self._logger.info(
                "scheduler_execution_handler.workflow_completed",
                workflow_id=event.workflow_id.value,
                executions_updated=len(executions),
            )

    async def handle_workflow_failed(self, event: WorkflowFailedEvent) -> None:
        now = self._clock.now()
        async with self._uow as uow:
            executions = await uow.scheduler_executions.get_by_action_ref(
                event.workflow_id.value,
            )
            if not executions:
                return

            for execution in executions:
                if execution.status.value != "executing":
                    continue

                events = self._orchestrator.complete_execution(
                    execution,
                    output_state=None,
                    error=event.error or "workflow_failed",
                    now=now,
                )
                await uow.scheduler_executions.save(execution)
                uow.stage_events(events)

            await uow.commit()

            self._logger.info(
                "scheduler_execution_handler.workflow_failed",
                workflow_id=event.workflow_id.value,
                error=event.error,
            )
