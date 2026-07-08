from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AgentConfigExecutionGetByIdQuery:
    agent_config_execution_id: str
