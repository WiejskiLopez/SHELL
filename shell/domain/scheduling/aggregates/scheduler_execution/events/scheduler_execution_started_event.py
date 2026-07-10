from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.action_ref import (
        ActionRef,
    )
    from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.action_ref_type import (
        ActionRefType,
    )
    from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id import (
        SchedulerExecutionId,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class SchedulerExecutionStartedEvent(DomainEvent):
    execution_id: SchedulerExecutionId
    action_ref: ActionRef
    action_ref_type: ActionRefType
