from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateGraphNodeExecutionCommand:
    graph_execution_id: str
    graph_node_definition_id: str
    position: int | None = None
    role: str | None = None
    mode: str | None = None
    node_type: str | None = None
    remaining_retries: int | None = None
    retry_delay_seconds: int | None = None
    timeout_seconds: int | None = None

    def __post_init__(self) -> None:
        if not self.graph_execution_id:
            raise ValueError("graph_execution_id cannot be empty")
        if not self.graph_node_definition_id:
            raise ValueError("graph_node_definition_id cannot be empty")
