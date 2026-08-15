from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SessionExecutionDto:
    id: str
    created_at: datetime
    user_execution_id: str | None = None
    session_id: str | None = None
