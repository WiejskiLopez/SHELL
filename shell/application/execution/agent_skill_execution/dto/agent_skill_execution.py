from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class AgentSkillExecutionDto:
    id: str
    agent_execution_id: str
    skill_data: dict[str, Any]
    created_at: datetime | None = None
