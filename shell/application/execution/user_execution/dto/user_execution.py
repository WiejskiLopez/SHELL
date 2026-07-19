from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class UserExecutionDto:
    id: str
    created_at: datetime
    user_id: str | None = None
