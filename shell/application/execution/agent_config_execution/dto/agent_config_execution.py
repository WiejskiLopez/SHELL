from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AgentConfigExecutionDto:
    id: str
    agent_execution_id: str
    config_data: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
