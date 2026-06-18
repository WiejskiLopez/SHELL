from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunGraphNodeExecutionCommand:
    workflow_id: str
    graph_node_execution_id: str
    workspace_path: str


@dataclass(frozen=True, slots=True)
class SaveGraphNodeExecutionResultCommand:
    workflow_id: str
    graph_node_execution_id: str
    status: str
    stdout: str = ""
    stderr: str = ""
    artifact_uri: str = ""
