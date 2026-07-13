from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class SessionExecutionStateDto:
    id: str
    session_execution_id: str
    direction: str
    state_data: dict[str, Any]
    created_at: datetime
