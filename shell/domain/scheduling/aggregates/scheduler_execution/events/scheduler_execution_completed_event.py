from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id import (
        SchedulerExecutionId,
    )
    from shell.platform.domain.value_objects.state_data import StateData


@dataclass(frozen=True, slots=True, kw_only=True)
class SchedulerExecutionCompletedEvent(DomainEvent):
    execution_id: SchedulerExecutionId
    output_state: StateData | None = None
