from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class UserExecutionDto:
    id: str
    user_id: str | None = None
    created_at: datetime | None = None
