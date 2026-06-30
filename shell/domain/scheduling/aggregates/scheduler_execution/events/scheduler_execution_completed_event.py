from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.state_data import StateData

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.scheduling.value_objects.ids import SchedulerExecutionId
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion


@dataclass(frozen=True, slots=True, kw_only=True)
class SchedulerExecutionCompletedEvent(DomainEvent):
    execution_id: SchedulerExecutionId
    output_state: StateData | None = None

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            execution_id=payload["execution_id"],
            output_state=StateData(payload["output_state"]) if payload["output_state"] else None,
            schema_version=SchemaVersion(schema_version),
        )
