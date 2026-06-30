from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AttachGraphNodeExecutionsCommand:
    graph_execution_id: str
    graph_node_definition_executions: dict[str, str]

    def __post_init__(self) -> None:
        if not self.graph_execution_id:
            raise ValueError("graph_execution_id cannot be empty")
        if not self.graph_node_definition_executions:
            raise ValueError("graph_node_definition_executions cannot be empty")
