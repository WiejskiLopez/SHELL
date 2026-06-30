from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SaveGraphNodeExecutionResultCommand:
    workflow_id: str
    graph_node_execution_id: str
    status: str
    stdout: str = ""
    stderr: str = ""
    artifact_uri: str = ""

    def __post_init__(self) -> None:
        if not self.workflow_id:
            raise ValueError("workflow_id cannot be empty")
        if not self.graph_node_execution_id:
            raise ValueError("graph_node_execution_id cannot be empty")
        if not self.status:
            raise ValueError("status cannot be empty")
