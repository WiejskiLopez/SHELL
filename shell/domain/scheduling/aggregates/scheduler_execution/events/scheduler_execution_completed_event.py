from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.state_data import StateData
    from shell.domain.scheduling.value_objects.ids import SchedulerExecutionId


@dataclass(frozen=True, slots=True, kw_only=True)
class SchedulerExecutionCompletedEvent(DomainEvent):
    execution_id: SchedulerExecutionId
    output_state: StateData | None = None
