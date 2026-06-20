from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.platform.events import DomainEvent
from shell.domain.scheduling.value_objects.ids import (
    SchedulerDefinitionId,
    SchedulerExecutionId,
)


@dataclass(frozen=True, slots=True)
class SchedulerExecutionFailedEvent(DomainEvent):
    scheduler_execution_id: SchedulerExecutionId
    scheduler_definition_id: SchedulerDefinitionId
    error: str
    action_ref: str | None = None

    @classmethod
    def now(
        cls,
        scheduler_execution_id: SchedulerExecutionId,
        scheduler_definition_id: SchedulerDefinitionId,
        error: str,
        action_ref: str | None = None,
        now: datetime | None = None,
    ) -> SchedulerExecutionFailedEvent:
        from datetime import datetime as dt

        return cls(
            occurred_at=now or dt.now(),
            scheduler_execution_id=scheduler_execution_id,
            scheduler_definition_id=scheduler_definition_id,
            error=error,
            action_ref=action_ref,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            scheduler_execution_id=SchedulerExecutionId(payload["scheduler_execution_id"]),
            scheduler_definition_id=SchedulerDefinitionId(payload["scheduler_definition_id"]),
            error=payload.get("error", ""),
            action_ref=payload.get("action_ref"),
        )
