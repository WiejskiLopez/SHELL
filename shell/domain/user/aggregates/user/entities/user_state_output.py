from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from shell.domain.user.value_objects.user_id import UserId

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class UserStateOutput:
    user_id: UserId
    payload: dict[str, Any]
    created_at: datetime
