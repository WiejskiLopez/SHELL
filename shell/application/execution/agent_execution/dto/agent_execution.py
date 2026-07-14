from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AgentExecutionDto:
    id: str
    node_execution_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
