from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.scheduling.ports.workflow_outcome_receiver import WorkflowOutcomeReceiver

if TYPE_CHECKING:
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.scheduling.services.scheduler_orchestrator import (
        SchedulerOrchestrator,
    )


class SchedulerExecutionHandler(WorkflowOutcomeReceiver):
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

    async def on_workflow_completed(self, workflow_id: str) -> None:
        now = self._clock.now()
        async with self._uow as uow:
            executions = await uow.scheduler_executions.get_by_action_ref(workflow_id)
            if not executions:
                self._logger.info(
                    "scheduler_execution_handler.no_matching_execution",
                    workflow_id=workflow_id,
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

            self._logger.info(
                "scheduler_execution_handler.workflow_completed",
                workflow_id=workflow_id,
                executions_updated=len(executions),
            )

    async def on_workflow_failed(self, workflow_id: str, error: str) -> None:
        now = self._clock.now()
        async with self._uow as uow:
            executions = await uow.scheduler_executions.get_by_action_ref(workflow_id)
            if not executions:
                return

            for execution in executions:
                if execution.status.value != "executing":
                    continue

                events = self._orchestrator.complete_execution(
                    execution,
                    output_state=None,
                    error=error,
                    now=now,
                )
                await uow.scheduler_executions.save(execution)
                uow.stage_events(events)

            self._logger.info(
                "scheduler_execution_handler.workflow_failed",
                workflow_id=workflow_id,
                error=error,
            )
