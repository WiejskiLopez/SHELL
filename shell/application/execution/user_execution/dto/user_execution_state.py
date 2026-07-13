from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from shell.platform.types import JsonStr


@dataclass(frozen=True, slots=True)
class UserExecutionStateDto:
    id: str
    user_execution_id: str
    direction: str
    state_data: JsonStr
    created_at: datetime

