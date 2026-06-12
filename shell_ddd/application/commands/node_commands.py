from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunNodeCommand:
    workflow_id: str
    node_id: str
    workspace_path: str


@dataclass(frozen=True, slots=True)
class SaveNodeResultCommand:
    workflow_id: str
    node_id: str
    status: str
    stdout: str = ""
    stderr: str = ""
    artifact_uri: str = ""
