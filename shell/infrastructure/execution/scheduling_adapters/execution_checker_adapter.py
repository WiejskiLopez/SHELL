from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.platform.ports.logging import Logger
    from shell.domain.scheduling.aggregates.scheduler_definition import (
        SchedulerDefinition,
    )
    from shell.domain.scheduling.aggregates.scheduler_execution import (
        SchedulerExecution,
    )
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class ExecutionCheckerAdapter:
    def __init__(
        self,
        uow: UnitOfWork,
        logger: Logger,
    ) -> None:
        self._uow = uow
        self._logger = logger

    async def can_execute(
        self,
        *,
        definition: SchedulerDefinition,
        execution: SchedulerExecution,
    ) -> bool:
        max_concurrent = definition.execution_policy.max_concurrent
        if max_concurrent <= 0:
            return True

        async with self._uow as uow:
            current = await uow.scheduler_executions.count_by_definition_and_status(
                scheduler_definition_id=definition.id.value,
                status="executing",
            )
            can = current < max_concurrent

            if not can:
                self._logger.info(
                    "execution_checker_adapter.max_concurrent_reached",
                    definition_id=definition.id.value,
                    current=current,
                    max_concurrent=max_concurrent,
                )

            return can
