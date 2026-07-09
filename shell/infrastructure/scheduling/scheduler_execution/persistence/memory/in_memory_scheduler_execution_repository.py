from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.scheduling.aggregates.scheduler_execution.scheduler_execution import (
    SchedulerExecution,
)
from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.count_result import (
    CountResult,
)
from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id import (
    SchedulerExecutionId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
        SchedulerDefinitionId,
    )
    from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.action_ref import (
        ActionRef,
    )
    from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.execution_status import (
        ExecutionStatus,
    )


class InMemorySchedulerExecutionRepository(
    InMemoryRepository[SchedulerExecution, SchedulerExecutionId]
):
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
