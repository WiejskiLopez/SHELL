from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AgentConfigExecutionDto:
    id: str
    agent_execution_id: str
    session_execution_id: str | None = None
    user_execution_id: str | None = None
    model: str = ""
    temperature: float = 0.0
    max_tokens: int = 0
    top_p: float = 0.0
    created_at: datetime | None = None
    updated_at: datetime | None = None
