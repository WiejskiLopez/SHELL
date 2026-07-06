from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateEdgeLinkExecutionCommand:
    node_execution_id: str
    edge_execution_id: str

    def __post_init__(self) -> None:
        if not self.node_execution_id:
            raise ValueError("node_execution_id cannot be empty")
        if not self.edge_execution_id:
            raise ValueError("edge_execution_id cannot be empty")
