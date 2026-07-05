from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.error_description import ErrorDescription
    from shell.domain.scheduling.value_objects.ids import SchedulerExecutionId


@dataclass(frozen=True, slots=True, kw_only=True)
class SchedulerExecutionFailedEvent(DomainEvent):
    execution_id: SchedulerExecutionId
    error: ErrorDescription | None = None
