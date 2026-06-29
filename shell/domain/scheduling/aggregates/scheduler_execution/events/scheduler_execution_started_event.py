from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from shell.domain.platform.events import DomainEvent
from shell.domain.scheduling.value_objects.action_ref import ActionRef
from shell.domain.scheduling.value_objects.action_ref_type import ActionRefType

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.scheduling.value_objects.ids import SchedulerExecutionId
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion


@dataclass(frozen=True, slots=True, kw_only=True)
class SchedulerExecutionStartedEvent(DomainEvent):
    execution_id: SchedulerExecutionId
    action_ref: ActionRef
    action_ref_type: ActionRefType

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            execution_id=payload["execution_id"],
            action_ref=ActionRef(payload["action_ref"]),
            action_ref_type=ActionRefType(payload["action_ref_type"]),
            schema_version=SchemaVersion(schema_version),
        )
