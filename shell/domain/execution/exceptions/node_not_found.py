from __future__ import annotations

from shell.domain.platform.exceptions.domain_error import DomainError


class NodeNotFound(DomainError):
    def __init__(self, graph_node_execution_id: str) -> None:
        super().__init__(f"Node not found: {graph_node_execution_id!r}")
