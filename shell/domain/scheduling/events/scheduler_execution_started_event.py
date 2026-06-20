from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.scheduling.value_objects.ids import SchedulerExecutionId


@dataclass(frozen=True, slots=True, kw_only=True)
class SchedulerExecutionStartedEvent(DomainEvent):
    execution_id: SchedulerExecutionId
    action_ref: str
    action_ref_type: str

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            execution_id=payload["execution_id"],
            action_ref=payload["action_ref"],
            action_ref_type=payload["action_ref_type"],
            schema_version=schema_version,
        )
