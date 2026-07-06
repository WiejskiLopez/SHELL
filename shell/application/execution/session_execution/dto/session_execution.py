from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class SessionExecutionDto:
    id: str
    user_execution_id: str | None = None
    session_id: str | None = None
    created_at: datetime | None = None
