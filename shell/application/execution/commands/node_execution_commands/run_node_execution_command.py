from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunNodeExecutionCommand:
    workflow_id: str
    node_execution_id: str
    workspace_path: str

    def __post_init__(self) -> None:
        if not self.workflow_id:
            raise ValueError("workflow_id cannot be empty")
        if not self.node_execution_id:
            raise ValueError("node_execution_id cannot be empty")
