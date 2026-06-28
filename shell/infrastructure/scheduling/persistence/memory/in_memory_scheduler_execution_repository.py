from __future__ import annotations

from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.execution_status import (
    ExecutionStatus,
)
from shell.domain.scheduling.value_objects.action_ref import ActionRef
from shell.domain.scheduling.value_objects.count_result import CountResult
from shell.domain.scheduling.aggregates.scheduler_execution.scheduler_execution import (
    SchedulerExecution,
)
from shell.domain.scheduling.value_objects.ids import (
    SchedulerDefinitionId,
    SchedulerExecutionId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository


class InMemorySchedulerExecutionRepository(InMemoryRepository[SchedulerExecution, SchedulerExecutionId]):

    async def get_by_action_ref(self, action_ref: ActionRef) -> list[SchedulerExecution]:
        return [e for e in self._store.values() if e.action_ref == action_ref]

    async def count_by_definition_and_status(
        self, scheduler_definition_id: SchedulerDefinitionId, status: ExecutionStatus
    ) -> CountResult:
        return CountResult(
            sum(
                1
                for e in self._store.values()
                if e.scheduler_definition_id == scheduler_definition_id and e.status == status
            )
        )
