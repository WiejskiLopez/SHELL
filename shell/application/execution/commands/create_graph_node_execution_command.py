from __future__ import annotations

from dataclasses import dataclass

_ROLE_VALUES = {"PLANNER", "AGENT", "TOOL", "VERIFIER"}
_MODE_VALUES = {"agent", "router", "tasker", "tool", "worker", "planner", "verifier"}


@dataclass(frozen=True, slots=True)
class CreateGraphNodeExecutionCommand:
    graph_execution_id: str
    graph_node_definition_id: str
    position: int
    role: str
    mode: str
    node_type: str

    def __post_init__(self) -> None:
        if not self.graph_execution_id:
            raise ValueError("graph_execution_id cannot be empty")
        if not self.graph_node_definition_id:
            raise ValueError("graph_node_definition_id cannot be empty")
        if not self.role:
            raise ValueError("role cannot be empty")
        if self.role not in _ROLE_VALUES:
            raise ValueError(f"role must be one of {_ROLE_VALUES}, got {self.role!r}")
        if not self.mode:
            raise ValueError("mode cannot be empty")
        if self.mode not in _MODE_VALUES:
            raise ValueError(f"mode must be one of {_MODE_VALUES}, got {self.mode!r}")
        if self.position < 0:
            raise ValueError(f"position must be >= 0, got {self.position}")
