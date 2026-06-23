from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from shell.domain.user.value_objects.user_id import UserId

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class UserSkill:
    id: str
    user_id: UserId
    payload: dict[str, Any]
    created_at: datetime

    @classmethod
    def new(cls, user_id: UserId, payload: dict[str, Any], now: datetime) -> UserSkill:
        return cls(id=str(uuid.uuid4()), user_id=user_id, payload=payload, created_at=now)
