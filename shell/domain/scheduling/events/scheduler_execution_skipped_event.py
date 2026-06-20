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
class SchedulerExecutionSkippedEvent(DomainEvent):
    scheduler_execution_id: SchedulerExecutionId
    scheduler_definition_id: SchedulerDefinitionId
    reason: str

    @classmethod
    def now(
        cls,
        scheduler_execution_id: SchedulerExecutionId,
        scheduler_definition_id: SchedulerDefinitionId,
        reason: str,
        now: datetime | None = None,
    ) -> SchedulerExecutionSkippedEvent:
        from datetime import datetime as dt

        return cls(
            occurred_at=now or dt.now(),
            scheduler_execution_id=scheduler_execution_id,
            scheduler_definition_id=scheduler_definition_id,
            reason=reason,
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
            reason=payload.get("reason", ""),
        )
