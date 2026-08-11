from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetAgentSkillExecutionByIdQuery:
    agent_skill_execution_id: str
