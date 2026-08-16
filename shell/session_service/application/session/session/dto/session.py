from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SessionDto:
    id: str
    user_id: str
    status: str
    opened_at: datetime
    closed_at: datetime | None
    created_at: datetime
    changed_at: datetime | None = None
    deleted_at: datetime | None = None
