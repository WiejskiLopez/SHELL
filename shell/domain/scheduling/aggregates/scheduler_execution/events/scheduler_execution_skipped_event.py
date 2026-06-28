from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from shell.domain.execution.value_objects.reason import Reason
from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.scheduling.value_objects.ids import SchedulerExecutionId


@dataclass(frozen=True, slots=True, kw_only=True)
class SchedulerExecutionSkippedEvent(DomainEvent):
    execution_id: SchedulerExecutionId
    reason: Reason

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            execution_id=payload.get("execution_id"),
            reason=Reason(payload.get("reason")),
            schema_version=schema_version,
        )
