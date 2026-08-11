from __future__ import annotations

from shell.platform.domain.exceptions.domain_error import DomainError


class NodeExecutionNotFoundError(DomainError):
    def __init__(self, node_execution_id: str) -> None:
        self.node_execution_id = node_execution_id
        super().__init__(f"Node execution not found: {node_execution_id!r}")
