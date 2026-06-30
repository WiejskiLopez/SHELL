from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.exists_result import ExistsResult
    from shell.domain.scheduling.aggregates.scheduler_execution.scheduler_execution import (
        SchedulerExecution,
    )
    from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.execution_status import (
        ExecutionStatus,
    )
    from shell.domain.scheduling.value_objects.action_ref import ActionRef
    from shell.domain.scheduling.value_objects.count_result import CountResult
    from shell.domain.scheduling.value_objects.ids import (
        SchedulerDefinitionId,
        SchedulerExecutionId,
    )


class SchedulerExecutionRepository(Protocol):
    async def get_by_id(self, id: SchedulerExecutionId) -> SchedulerExecution | None: ...

    async def delete(self, id: SchedulerExecutionId) -> None: ...
    async def exists(self, id: SchedulerExecutionId) -> ExistsResult: ...

    async def get_by_action_ref(self, action_ref: ActionRef) -> list[SchedulerExecution]: ...

    async def count_by_definition_and_status(
        self, scheduler_definition_id: SchedulerDefinitionId, status: ExecutionStatus
    ) -> CountResult: ...

    async def save(self, execution: SchedulerExecution) -> None: ...
