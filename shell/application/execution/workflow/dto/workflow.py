from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class WorkflowDto:
    id: str
    status: str
    created_at: datetime
    session_id: str | None = None
