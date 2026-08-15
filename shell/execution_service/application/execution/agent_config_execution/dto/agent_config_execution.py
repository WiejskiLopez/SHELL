from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AgentConfigExecutionDto:
    id: str
    agent_execution_id: str
    created_at: datetime
    config_data: str = ""
    changed_at: datetime | None = None
