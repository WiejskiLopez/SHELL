from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
    UserExecutionId,
)
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class UserExecutionCreatedEvent(DomainEvent):
    user_execution_id: UserExecutionId

    @classmethod
    def now(
        cls,
        user_execution_id: UserExecutionId,
        now: datetime,
    ) -> UserExecutionCreatedEvent:
        return cls(
            occurred_at=now,
            user_execution_id=user_execution_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            user_execution_id=UserExecutionId(payload["user_execution_id"]),
        )
