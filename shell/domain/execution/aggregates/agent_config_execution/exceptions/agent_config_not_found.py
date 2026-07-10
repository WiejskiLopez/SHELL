from __future__ import annotations

from shell.platform.domain.exceptions.domain_error import DomainError


class AgentConfigNotFound(DomainError):
    def __init__(self, agent_config_execution_id: str) -> None:
        super().__init__(f"AgentConfigExecution not found: {agent_config_execution_id!r}")
