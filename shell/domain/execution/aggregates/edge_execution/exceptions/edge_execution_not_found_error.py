from __future__ import annotations

from shell.platform.domain.exceptions.domain_error import DomainError


class EdgeExecutionNotFoundError(DomainError):
    def __init__(self, edge_execution_id: str) -> None:
        super().__init__(f"EdgeExecution '{edge_execution_id}' not found")
