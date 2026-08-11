from __future__ import annotations

from shell.platform.domain.exceptions.domain_error import DomainError


class EdgeLinkExecutionNotFoundError(DomainError):
    def __init__(self, edge_link_execution_id: str) -> None:
        super().__init__(f"EdgeLinkExecution '{edge_link_execution_id}' not found")
