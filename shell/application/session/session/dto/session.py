from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SessionDto:
    id: str
    goal: str
    status: str
    opened_at: datetime
    closed_at: datetime | None
