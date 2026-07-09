from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetAgentExecutionByIdQuery:
    agent_execution_id: str
