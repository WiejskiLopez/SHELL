from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.platform.events import DomainEvent
from shell.domain.user.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class UserDisabledEvent(DomainEvent):
    user_id: UserId

    @classmethod
    def now(cls, user_id: UserId, now: datetime) -> UserDisabledEvent:
        return cls(occurred_at=now, user_id=user_id)

    @classmethod
    def from_payload(cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1) -> Self:
        return cls(occurred_at=occurred_at, schema_version=schema_version, user_id=UserId(payload["user_id"]))
