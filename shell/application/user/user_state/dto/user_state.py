from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class UserStateDto:
    id: str
    user_id: str
    direction: str
    state_data: dict[str, Any]
    created_at: datetime | None = None
