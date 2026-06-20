from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.scheduling.ports.scheduler_execution_checker import SchedulerExecutionChecker
    from shell.domain.scheduling.ports.graph_execution_launcher import (
        GraphExecutionLauncher,
    )
    from shell.domain.scheduling.services.scheduler_orchestrator import (
        SchedulerOrchestrator,
    )


class SchedulerTriggerHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        logger: Logger,
        orchestrator: SchedulerOrchestrator,
        launcher: GraphExecutionLauncher,
        checker: SchedulerExecutionChecker,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._logger = logger
        self._orchestrator = orchestrator
        self._launcher = launcher
        self._checker = checker

    async def handle(self, event: DomainEvent) -> None:
        source_context = "execution"
        trigger_event_type = type(event).__name__

        trigger_event_id = str(
            getattr(event, "workflow_id", getattr(event, "id", ""))
        )

        input_state: dict = {}
        if hasattr(event, "payload") and isinstance(event.payload, dict):
            input_state = event.payload
        elif hasattr(event, "combined_output") and event.combined_output:
            input_state = event.combined_output

        correlation_id = getattr(event, "correlation_id", "")
        now = self._clock.now()

        async with self._uow as uow:
            definitions = await uow.scheduler_definitions.find_by_trigger(
                source_context=source_context,
                trigger_event_type=trigger_event_type,
            )

            if not definitions:
                return

            for definition in definitions:
                execution = self._orchestrator.evaluate_definition(
                    definition=definition,
                    trigger_event_id=trigger_event_id,
                    trigger_event_type=trigger_event_type,
                    input_state=input_state,
                    can_execute=False,
                    now=now,
                )

                if execution.status.value == "skipped":
                    await uow.scheduler_executions.save(execution)
                    uow.stage_events(execution.pull_events())
                    continue

                can_run = await self._checker.can_execute(
                    definition=definition,
                    execution=execution,
                )

                if not can_run:
                    execution.skip(reason="execution_checker rejected", now=now)
                    await uow.scheduler_executions.save(execution)
                    uow.stage_events(execution.pull_events())
                    continue

                graph_def_id = definition.action_config.graph_definition_id
                if graph_def_id is None:
                    execution.skip(reason="no graph_definition_id", now=now)
                    await uow.scheduler_executions.save(execution)
                    uow.stage_events(execution.pull_events())
                    continue

                graph_execution_id = await self._launcher.launch(
                    graph_definition_id=graph_def_id,
                    input_state=execution.input_state,
                    correlation_id=correlation_id,
                )

                events = self._orchestrator.start_execution(
                    execution,
                    action_ref=graph_execution_id,
                    action_ref_type="graph_execution",
                    now=now,
                )

                await uow.scheduler_executions.save(execution)
                uow.stage_events(events)

            self._logger.info(
                "scheduler_trigger_handler.processed",
                source_context=source_context,
                trigger_event_type=trigger_event_type,
                definition_count=len(definitions),
            )
