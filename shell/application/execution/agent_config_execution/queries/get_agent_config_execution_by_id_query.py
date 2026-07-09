from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetAgentConfigExecutionByIdQuery:
    agent_config_execution_id: str
